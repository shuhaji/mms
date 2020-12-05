# -*- coding: utf-8 -*-

from datetime import datetime
import time
from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class ReportPartnerLedger(models.AbstractModel):
    _inherit = 'report.account.report_partnerledger'

    def _lines(self, data, partner):
        full_account = []
        currency = self.env['res.currency']
        query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()

        # edit by mario ardi
        # reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".full_reconcile_id IS NULL '
        reconcile_clause = ""
        params = [tuple(data['computed']['partner_ids']), tuple(data['computed']['move_state']), tuple(data['computed']['account_ids'])] + query_get_data[2]
        query = """
            SELECT "account_move_line".id, "account_move_line".date,ai.name as ref_desc, "account_move_line".partner_id, "account_move_line".date_maturity, 
            j.code, UPPER(j.name) as journal_name, acc.code as a_code, acc.name as a_name, "account_move_line".ref, 
            case when "account_move_line".payment_id is not null then ap.name else m.name end as move_name, 
            "account_move_line".name, "account_move_line".debit, "account_move_line".credit, "account_move_line".amount_currency,
            "account_move_line".currency_id, c.symbol AS currency_code, ai."type" as ai_type,
             case when "account_move_line".invoice_id is not null then ai.app_source
                when "account_move_line".payment_id is not null then ap.app_source
             else '' end as app_source,
             case when "account_move_line".invoice_id is not null then 'INVOICE'
                when "account_move_line".payment_id is not null then 'PAYMENT'
                when "account_move_line".withholding_tax_generated_by_move_id is not null then 'WH_TAX'
             else '' end as source_type
            FROM """ + query_get_data[0] + """
            LEFT JOIN account_journal j ON ("account_move_line".journal_id = j.id)
            LEFT JOIN account_account acc ON ("account_move_line".account_id = acc.id)
            LEFT JOIN res_currency c ON ("account_move_line".currency_id=c.id)
            LEFT JOIN account_move m ON (m.id="account_move_line".move_id)
            LEFT JOIN account_payment ap ON ("account_move_line".payment_id = ap.id)
            LEFT JOIN account_invoice ai ON ("account_move_line".invoice_id = ai.id)
            WHERE "account_move_line".partner_id IN %s                                
                AND m.state IN %s                
                AND "account_move_line".account_id IN %s                 
                AND """ + query_get_data[1] + reconcile_clause + """ 
                AND left(coalesce(account_move_line.ref,''),3)<>'POS'               
                ORDER BY "account_move_line".date ASC"""

        self.env.cr.execute(query, tuple(params))
        res = self.env.cr.dictfetchall()
        sum = 0.0
        lang_code = self.env.context.get('lang') or 'en_US'
        lang = self.env['res.lang']
        lang_id = lang._lang_get(lang_code)
        date_format = lang_id.date_format
        for r in res:
            # r['date'] = datetime.strptime(r['date'], DEFAULT_SERVER_DATE_FORMAT).strftime(date_format)
            r['displayed_name'] = '-'.join(
                r[field_name] for field_name in ('move_name', 'ref', 'name')
                if r[field_name] not in (None, '', '/')
            )
            sum += r['debit'] - r['credit']
            r['progress'] = sum
            r['currency_id'] = currency.browse(r.get('currency_id'))
            full_account.append(r)
        return full_account

    def _sum_partner(self, data, partner, field):
        if field not in ['debit', 'credit', 'debit - credit']:
            return
        result = 0.0
        query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
        # edit by mario ardi
        # reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".full_reconcile_id IS NULL '
        reconcile_clause = ""

        params = [tuple(data['computed']['partner_ids']), tuple(data['computed']['move_state']), tuple(data['computed']['account_ids'])] + query_get_data[2]
        query = """SELECT sum(""" + field + """)
                FROM """ + query_get_data[0] + """, account_move AS m
                WHERE "account_move_line".partner_id IN %s
                    AND m.id = "account_move_line".move_id
                    AND m.state IN %s
                    AND account_id IN %s
                    AND """ + query_get_data[1] + reconcile_clause
        self.env.cr.execute(query, tuple(params))

        contemp = self.env.cr.fetchone()
        if contemp is not None:
            result = contemp[0] or 0.0
        return result

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        data['computed'] = {}
        query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
        data['computed']['move_state'] = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            data['computed']['move_state'] = ['posted']
        result_selection = data['form'].get('result_selection', 'customer')
        account_id = []
        partner_id = []
        if result_selection == 'supplier':
            data['computed']['ACCOUNT_TYPE'] = ['payable']
            account_id = data['form'].get('ap_account_id')[0] if data['form'].get('ap_account_id') else False
            partner_id = 'supplier_id' in data['form'] and data['form']['supplier_id'] or False
        elif result_selection == 'customer':
            data['computed']['ACCOUNT_TYPE'] = ['receivable']
            account_id = data['form'].get('ar_account_id')[0] if data['form'].get('ar_account_id') else False
            partner_id = 'customer_id' in data['form'] and data['form']['customer_id'] or False
        else:
            data['computed']['ACCOUNT_TYPE'] = ['payable', 'receivable']

        query = '''
            SELECT a.id
            FROM account_account a
            WHERE a.internal_type IN %s
            AND NOT a.deprecated
            '''
        arg_list = (tuple(data['computed']['ACCOUNT_TYPE']),)
        if account_id:
            query += ''' AND a.id = %s '''
            arg_list += (account_id,)

        self.env.cr.execute(query, arg_list)
        data['computed']['account_ids'] = [a for (a,) in self.env.cr.fetchall()]

        params = [tuple(data['computed']['move_state']), tuple(data['computed']['account_ids'])] + query_get_data[2]

        # edit by mario ardi
        # reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".full_reconcile_id IS NULL '
        reconcile_clause = ""

        # if not partner_ids:
        query = """
            SELECT DISTINCT "account_move_line".partner_id
            FROM """ + query_get_data[0] + """, account_account AS account, account_move AS am
            WHERE "account_move_line".partner_id IS NOT NULL
                AND "account_move_line".account_id = account.id
                AND am.id = "account_move_line".move_id
                AND am.state IN %s
                AND "account_move_line".account_id IN %s
                AND NOT account.deprecated
                AND """ + query_get_data[1] + reconcile_clause
        if partner_id:
            query += ''' AND "account_move_line".partner_id IN %s '''
            params += (tuple(partner_id),)

        self.env.cr.execute(query, tuple(params))
        partner_ids = [res['partner_id'] for res in self.env.cr.dictfetchall()]
        data['computed']['partner_ids'] = partner_ids

        obj_partner = self.env['res.partner']
        partners = obj_partner.browse(partner_ids)
        partners = sorted(partners, key=lambda x: (x.ref or '', x.name or ''))

        return {
            'doc_ids'       : partner_ids,
            'doc_model'     : self.env['res.partner'],
            'data'          : data,
            'docs'          : partners[0] if partners else False,
            'docs_data'     : partners,
            'time'          : time,
            'lines'         : self._lines,
            'sum_partner'   : self._sum_partner,
        }
