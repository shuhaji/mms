from odoo import api, fields, models, _


class WizardPartnerLedger(models.TransientModel):
    _inherit = ['wizard.kg.report.base', 'account.report.partner.ledger']
    _name = 'wizard.kg.report.partner.ledger'
    _title = "KG Report - Partner Ledger"

    # partner_id = fields.Many2many(
    #     comodel_name='res.partner',
    #     string='Partner',
    #     required=False,
    # )
    ap_account_id = fields.Many2one('account.account', string='Account Payable')
    ar_account_id = fields.Many2one('account.account', string='Account Receivable')
    supplier_id = fields.Many2many('res.partner', string='Partner')
    customer_id = fields.Many2many('res.partner', string='Partner')

    @api.onchange('ap_account_id', 'ar_account_id')
    def onchange_account_id(self):
        if not self.ap_account_id:
            self.supplier_id = None
        elif not self.ar_account_id:
            self.customer_id = None

    @api.multi
    def _get_data(self):
        get_partner_ledger = self.get_partner_ledger_data()
        self.report_has_logo = False  # sample report has logo

        data = {
            'config': {
                'start_date': self.date_from,
                'end_date': self.date_to or '',
                'company_id': self.company_id.name,
                'partner_id': '',
                "company_address": "{street} {street2} {city} {state} {zip} {country}".format(
                    street=self.company_id.street or "",
                    street2=self.company_id.street2 or "",
                    city=self.company_id.city or "",
                    state=self.company_id.state_id.name if self.company_id.state_id else "",
                    zip=self.company_id.zip or "",
                    country=self.company_id.country_id.name if self.company_id.country_id else "",
                ),
                'printed_by': self.env.user.name,
            },
            'data': get_partner_ledger
        }
        return data

    @api.multi
    def get_partner_ledger_data(self):
        where_account_clause, where_journal_clause, where_partner_clause, where_target_move_clause, where_result_selection_clause = self.query_get_clause()

        supplier_format_clause = tuple(self.supplier_id.ids)
        if len(self.supplier_id.ids) == 1:
            supplier_format_clause = (self.supplier_id.ids[0])

        customer_format_clause = tuple(self.customer_id.ids)
        if len(self.customer_id.ids) == 1:
            customer_format_clause = (self.customer_id.ids[0])

        journal_format_clause = tuple(self.journal_ids.ids)
        if len(self.journal_ids.ids) == 1:
            journal_format_clause = (self.journal_ids.ids[0])

        query = """                   
            WITH                 
            z_kg_move_line as (
                select acc.company_id, acc.id as account_id, l.partner_id,
                    row_number() over (
                        order by acc.company_id, acc.code, l.date
                    ) as row_no,                        
                    (COALESCE(l.debit,0)) as debit,
                    (COALESCE(l.credit, 0)) as credit,
                    (COALESCE(l.debit,0) - COALESCE(l.credit, 0)) AS balance
                    ,l.id, l.date as inv_date, l.currency_id, l.move_id, l.ref, l.name as name
                    , case when l.payment_id is not null then ap.name else m.name end as move_name
                    , j.code as journal_code, p.name as partner_name
                    , UPPER(j.name) as journal_name, l.date_maturity as due_date, coalesce(ai.name,'') as ref_desc
                    , case when l.invoice_id is not null then 'INVOICE'
                            when l.payment_id is not null then 'PAYMENT'
                            when l.withholding_tax_generated_by_move_id is not null then 'WH_TAX'
                         else '' end as source_type
                    , case when l.invoice_id is not null then ai.app_source
                            when l.payment_id is not null then ap.app_source
                         else '' end as app_source
                    , case when l.invoice_id is not null then (case when ai.type in ('out_refund', 'in_refund') then ai.name else '' end)
                            when l.payment_id is not null then concat('PAYMENT(',j.name,')')
                            when l.withholding_tax_generated_by_move_id is not null then concat('WH_TAX(',j.name,')')
                         else '' end as description 
                FROM  account_account acc
                    left join account_move_line l on (l.account_id = acc.id)  
                    left JOIN account_move m ON (l.move_id=m.id)                    
                    LEFT JOIN account_journal j ON (l.journal_id=j.id)  
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)
                    LEFT JOIN account_invoice ai ON (l.invoice_id = ai.id)
                    LEFT JOIN account_payment ap ON (l.payment_id = ap.id)
                where l.company_id = {company_id} 
                    AND l.date <= '{start_date}'
                    """ + where_account_clause + """
                    """ + where_partner_clause + """                    
                    """ + where_journal_clause + """                    
                    """ + where_target_move_clause + """
                    """ + where_result_selection_clause + """                     
            )
            SELECT acc.company_id, acc.id AS account_id, acc."name" as acc_name, acc.code as acc_code, zl.partner_id,  
                COALESCE(zl.debit,0) AS debit, 
                COALESCE(zl.credit,0) AS credit, 
                -1*COALESCE(zl.balance,0) as balance,
                (sum(-1*COALESCE(zl.balance,0)) over (
                        partition by acc.company_id, acc.code, zl.partner_id order by acc.company_id, acc.code, zl.partner_id, zl.row_no
                    )) as running_total_balance            
                , zl.row_no, zl.inv_date, zl.journal_code AS lcode 
                , zl.currency_id, zl.id AS lid, zl.ref AS lref, zl.name AS lname                  
                , zl.move_name, zl.partner_name
                , zl.journal_name, zl.due_date, zl.ref_desc
                , zl.source_type, zl.app_source, zl.description             
            FROM  account_account acc                
                left join z_kg_move_line zl on (zl.account_id = acc.id)                     
            WHERE acc.company_id = {company_id}
                """ + where_result_selection_clause + """ 
                AND (COALESCE(zl.balance,0) != 0)            
            ORDER BY acc.company_id, acc.code, zl.partner_id, zl.row_no;             
        """
        final_query = query.format(company_id=self.company_id.id,
                                   start_date=self.date_to,
                                   ap_account_id=self.ap_account_id.id,
                                   ar_account_id=self.ar_account_id.id,
                                   supplier_id=supplier_format_clause,
                                   customer_id=customer_format_clause,
                                   journal_ids=journal_format_clause)

        self.env.cr.execute(final_query)
        partner_ledger = self.env.cr.dictfetchall()

        return partner_ledger

    def query_get_clause(self):
        where_target_move_clause = ""
        if self.target_move == 'posted':
            where_target_move_clause = "AND m.state = 'posted'"

        where_journal_clause = ""
        if self.journal_ids:
            where_journal_clause = "and l.journal_id in {journal_ids}"
            if len(self.journal_ids.ids) == 1:
                where_journal_clause = "and l.journal_id = {journal_ids}"

        where_result_selection_clause = "and acc.internal_type in ('payable', 'receivable')"
        where_account_clause = ""
        where_partner_clause = "and l.partner_id is not null"

        if self.result_selection == 'supplier':
            where_result_selection_clause = "and acc.internal_type = 'payable'"

            if self.ap_account_id:
                where_account_clause = "and l.account_id = {ap_account_id}"

            if self.supplier_id:
                where_partner_clause = "and l.partner_id in {supplier_id}"
                if len(self.supplier_id.ids) == 1:
                    where_partner_clause = "and l.partner_id = {supplier_id}"

        elif self.result_selection == 'customer':
            where_result_selection_clause = "and acc.internal_type = 'receivable'"

            if self.ar_account_id:
                where_account_clause = "and l.account_id = {ar_account_id}"

            if self.customer_id:
                where_partner_clause = "and l.partner_id in {customer_id}"
                if len(self.customer_id.ids) == 1:
                    where_partner_clause = "and l.partner_id = {customer_id}"

        return where_account_clause, where_journal_clause, where_partner_clause, where_target_move_clause, where_result_selection_clause

    @staticmethod
    def _define_report_name():
        rpt = "/kg_account/static/rpt/PartnerLedger.mrt"
        return rpt

    # @api.multi
    # def _get_data(self):
    #     """ get data from database or any other source
    #
    #     :return: dict or list of dict
    #     """
    #     data = {}
    #     data['form'] = self.read(['date_from', 'date_to', 'ap_account_id', 'ar_account_id', 'supplier_id', 'customer_id',
    #                               'journal_ids', 'target_move', 'result_selection', 'amount_currency', 'reconciled'])[0]
    #     used_context = self._build_contexts(data)
    #     data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
    #
    #     res = self.get_report_values(data=data)
    #
    #     return {
    #         "config": {
    #             "start_date": self.date_from,
    #             "end_date": self.date_to or '',
    #             "partner_id": '',
    #             "company_id": self.company_id.name or '',
    #             "company_address": "{street} {street2} {city} {state} {zip} {country}".format(
    #                 street=self.company_id.street or "",
    #                 street2=self.company_id.street2 or "",
    #                 city=self.company_id.city or "",
    #                 state=self.company_id.state_id.name if self.company_id.state_id else "",
    #                 zip=self.company_id.zip or "",
    #                 country=self.company_id.country_id.name if self.company_id.country_id else "",
    #             ),
    #             "printed_by": self.env.user.name,
    #         },
    #         "data": res
    #     }
    #
    # def _build_contexts(self, data):
    #     result = {}
    #     result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
    #     result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
    #     result['date_from'] = data['form']['date_from'] or False
    #     result['date_to'] = data['form']['date_to'] or False
    #     result['strict_range'] = True if result['date_from'] else False
    #     return result
    #
    # def get_report_values(self, data=None):
    #     # from /local/kg_account/reports/account_partner_ledger.py
    #     res = self.env['report.account.report_partnerledger'].get_report_values(docids=None, data=data)
    #
    #     lines = []
    #     for p in res['docs_data']:
    #         balance = 0
    #         amount = 0
    #         desc = ''
    #         for line in self.env['report.account.report_partnerledger']._lines(data=data, partner=p):
    #             if line['source_type'] == 'PAYMENT':
    #                 desc = "PAYMENT" + ("(" + line['journal_name'] + ")" if line['move_name'] else "")
    #                 if line['debit'] > 0:
    #                     amount = -1 * line['debit']
    #                     balance -= line['debit']
    #                 if line['credit'] > 0:
    #                     amount = -1 * line['credit']
    #                     balance -= line['credit']
    #             elif line['source_type'] == 'INVOICE':
    #                 if line['ai_type'] == 'out_refund' or line['ai_type'] == 'in_refund':
    #                     desc = (line['ref_desc'] if line['move_name'] else "")
    #                     if line['debit'] > 0:
    #                         amount = -1 * line['debit']
    #                         balance -= line['debit']
    #                     if line['credit'] > 0:
    #                         amount = -1 * line['credit']
    #                         balance -= line['credit']
    #                 else:
    #                     desc = " "
    #                     if line['debit'] > 0:
    #                         amount = line['debit']
    #                         balance += line['debit']
    #                     if line['credit'] > 0:
    #                         amount = line['credit']
    #                         balance += line['credit']
    #             elif line['source_type'] == 'WH_TAX':
    #                 desc = "WHTAX" + ("(" + line['journal_name'] + ")" if line['move_name'] else "")
    #                 if line['debit'] > 0:
    #                     amount = -1 * line['debit']
    #                     balance -= line['debit']
    #                 if line['credit'] > 0:
    #                     amount = -1 * line['credit']
    #                     balance -= line['credit']
    #             else:
    #                 desc = " "
    #                 if line['debit'] > 0:
    #                     amount = line['debit']
    #                     balance += line['debit']
    #                 if line['credit'] > 0:
    #                     amount = -1 * line['credit']
    #                     balance -= line['credit']
    #
    #             lines.append({
    #                 "partner_name": p.name,
    #                 "account_name": line['a_name'],
    #                 "inv_date": line['date'],
    #                 "due_date": line['date_maturity'],
    #                 "inv_number": line['move_name'],
    #                 "source": line['app_source'],
    #                 "ref_no": line['ref'],
    #                 "description": desc,
    #                 "amount": amount,
    #                 "balance": balance,
    #             })
    #     return lines

