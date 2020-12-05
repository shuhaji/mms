# -*- coding: utf-8 -*-

import time
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from datetime import datetime
from dateutil.relativedelta import relativedelta


class KGAccountAgedPartnerBalance (models.TransientModel):
    _inherit = 'account.aged.trial.balance'

    def _print_report(self, data):
        res = {}
        data = self.pre_print_report(data)
        data['form'].update(self.read(['period_length'])[0])
        period_length = data['form']['period_length']
        if period_length<=0:
            raise UserError(_('You must set a period length greater than 0.'))
        if not data['form']['date_from']:
            raise UserError(_('You must set a start date.'))

        start = datetime.strptime(data['form']['date_from'], "%Y-%m-%d")

        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length - 1)

            # custom code to set custom period (e.g 0-30, 31-60, 61-90, 120+) 
            if i == 4:
                res[str(i)] = {
                    'name': (str((5-(i+1)) * period_length) + '-' + str((5-i) * period_length)),
                    'stop': start.strftime('%Y-%m-%d'),
                    'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
                }
            elif i == 1:
                res[str(i)] = {
                    'name': ('> '+str(3 * period_length)),
                    'stop': start.strftime('%Y-%m-%d'),
                    'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
                }
            else:
                res[str(i)] = {
                    'name': (i in [2, 3] and (str(((5-(i+1)) * period_length)+1) + '-' + str((5-i) * period_length)) or ('> '+str(4 * period_length))),
                    'stop': start.strftime('%Y-%m-%d'),
                    'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
                }
            # end of custom code
            
            # original code
            # res[str(i)] = {
            #     'name': (i!=0 and (str((5-(i+1)) * period_length) + '-' + str((5-i) * period_length)) or ('+'+str(4 * period_length))),
            #     'stop': start.strftime('%Y-%m-%d'),
            #     'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
            # }
            # end of original code

            start = stop - relativedelta(days=1)
        data['form'].update(res)
        return self.env.ref('account.action_report_aged_partner_balance').with_context(landscape=True).report_action(self, data=data)


class KGReportAgedPartnerBalance(models.AbstractModel):
    _inherit = 'report.account.report_agedpartnerbalance'

    def _get_partner_move_lines(self, account_type, date_from, target_move, period_length, account_id, partner_id):
        # This method can receive the context key 'include_nullified_amount' {Boolean}
        # Do an invoice and a payment and unreconcile. The amount will be nullified
        # By default, the partner wouldn't appear in this report.
        # The context key allow it to appear
        # In case of a period_length of 30 days as of 2019-02-08, we want the following periods:
        # Name       Stop         Start
        # 1 - 30   : 2019-02-07 - 2019-01-09
        # 31 - 60  : 2019-01-08 - 2018-12-10
        # 61 - 90  : 2018-12-09 - 2018-11-10
        # 91 - 120 : 2018-11-09 - 2018-10-11
        # +120     : 2018-10-10
        periods = {}
        start = datetime.strptime(date_from, "%Y-%m-%d")
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length)
            period_name = str((5-(i+1)) * period_length + 1) + '-' + str((5-i) * period_length)
            period_stop = (start - relativedelta(days=1)).strftime('%Y-%m-%d')
            if i == 0:
                period_name = '+' + str(4 * period_length)
            periods[str(i)] = {
                'name': period_name,
                'stop': period_stop,
                'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop
        res = []
        total = []
        cr = self.env.cr
        company_ids = self.env.context.get('company_ids', (self.env.user.company_id.id,))
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']
        arg_list = (tuple(move_state), tuple(account_type))

        # build the reconciliation clause to see what partner needs to be printed
        reconciliation_clause = '(l.reconciled IS FALSE)'
        cr.execute('SELECT debit_move_id, credit_move_id FROM account_partial_reconcile where create_date > %s', (date_from,))
        reconciled_after_date = []
        for row in cr.fetchall():
            reconciled_after_date += [row[0], row[1]]
        if reconciled_after_date:
            reconciliation_clause = '(l.reconciled IS FALSE OR l.id IN %s)'
            arg_list += (tuple(reconciled_after_date),)
        arg_list += (date_from, tuple(company_ids))
        query = '''
            SELECT DISTINCT l.partner_id, UPPER(p.name), l.account_id
            FROM account_move_line AS l left join res_partner AS p on l.partner_id = p.id
                left join account_account AS aa on l.account_id = aa.id
                left join account_move AS am on l.move_id = am.id                
            WHERE am.state IN %s
                AND aa.internal_type IN %s
                AND ''' + reconciliation_clause + '''
                AND (l.date <= %s)
                AND l.company_id IN %s     
            '''
        if account_id:
            query += ''' AND l.account_id = %s '''
            arg_list += (account_id, )
        if partner_id:
            query += ''' AND l.partner_id in %s '''
            # arg_list += (tuple(partner_id), ) if type(partner_id) is list else (tuple(partner_id))
            arg_list += (tuple(partner_id),)

        query += ''' ORDER BY UPPER(p.name)'''
        cr.execute(query, arg_list)

        partners = cr.dictfetchall()
        # put a total of 0
        for i in range(7):
            total.append(0)

        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['partner_id'] for partner in partners if partner['partner_id']]
        lines = dict((partner['partner_id'] or False, []) for partner in partners)
        if not partner_ids:
            return [], [], {}

        # adding filter by account n partner
        # account_clause = ''
        # partner_clause = 'AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))'
        # account_join = ''
        # if account_id:
        #     account_join = "left join res_partner AS p on l.partner_id = p.id " \
        #                    "left join ir_property sp on p.id = replace(sp.res_id, 'res.partner,', '')::int"
        #     if account_type == ['payable']:
        #         account_clause = "AND sp.name = 'property_account_payable_id' AND sp.value_reference = 'account.account,' || %s ::varchar"
        #         if partner_id:
        #             partner_ids = partner_id
        #     elif account_type == ['receivable']:
        #         account_clause = "AND sp.name = 'property_account_receivable_id' AND sp.value_reference = 'account.account,' || %s ::varchar"
        #         if partner_id:
        #             partner_ids = partner_id

        # This dictionary will store the not due amount of all partners
        undue_amounts = {}

        # custom code
        arg_list = (tuple(move_state), tuple(account_type), date_from, tuple(partner_ids), date_from, tuple(company_ids))

        query = '''
            SELECT l.id
            FROM account_move_line AS l left join account_account AS aa on l.account_id = aa.id
                left join account_move AS am on l.move_id = am.id
                left join account_invoice AS ai on ai.id = l.invoice_id                                
            WHERE am.state IN %s
                AND aa.internal_type IN %s
                AND COALESCE(ai.date_invoice,l.date) >= %s
                AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                AND (l.date <= %s)                
                AND l.company_id IN %s
            '''
        if account_id:
            query += ''' AND l.account_id = %s '''
            arg_list += (account_id, )

        query += ''' ORDER BY l.id '''

        cr.execute(query, arg_list)
        # end of custom code

        # original code
        # query = '''SELECT l.id
        #         FROM account_move_line AS l, account_account, account_move am
        #         WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
        #             AND (am.state IN %s)
        #             AND (account_account.internal_type IN %s)
        #             AND (COALESCE(l.date_maturity,l.date) >= %s)\
        #             AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
        #         AND (l.date <= %s)
        #         AND l.company_id IN %s'''
        # cr.execute(query, (tuple(move_state), tuple(account_type), date_from, tuple(partner_ids), date_from, tuple(company_ids)))
        # end of original code

        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        for line in self.env['account.move.line'].browse(aml_ids):
            partner_id = line.partner_id.id or False
            if partner_id not in undue_amounts:
                undue_amounts[partner_id] = 0.0
            line_amount = line.balance
            if line.balance == 0:
                continue
            for partial_line in line.matched_debit_ids:
                if partial_line.max_date <= date_from:
                    line_amount += partial_line.amount
            for partial_line in line.matched_credit_ids:
                if partial_line.max_date <= date_from:
                    line_amount -= partial_line.amount
            if not self.env.user.company_id.currency_id.is_zero(line_amount):
                undue_amounts[partner_id] += line_amount
                lines[partner_id].append({
                    'line': line,
                    'amount': line_amount,
                    'period': 6,
                })
        # Use one query per period and store results in history (a list variable)
        # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
        history = []
        for i in range(5):
            args_list = (tuple(move_state), tuple(account_type), tuple(partner_ids),)

            # custom code
            dates_query = '(COALESCE(ai.date_invoice,l.date)'
            # end of custom code

            # original code
            # dates_query = '(COALESCE(l.date_maturity,l.date)'
            # end of original code

            if periods[str(i)]['start'] and periods[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (periods[str(i)]['start'], periods[str(i)]['stop'])
            elif periods[str(i)]['start']:
                dates_query += ' >= %s)'
                args_list += (periods[str(i)]['start'],)
            else:
                dates_query += ' <= %s)'
                args_list += (periods[str(i)]['stop'],)
            args_list += (date_from, tuple(company_ids))

            # custom code
            query = '''SELECT l.id                    
                FROM account_move_line AS l left join account_account AS aa on l.account_id = aa.id
                    left join account_move AS am on l.move_id = am.id
                    left join account_invoice AS ai on ai.id = l.invoice_id 
                WHERE am.state IN %s
                    AND aa.internal_type IN %s
                    AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                    AND ''' + dates_query + '''
                    AND l.date <= %s
                    AND l.company_id IN %s
                '''
            if account_id:
                query += ''' AND l.account_id = %s '''
                args_list += (account_id, )

            query += '''ORDER BY l.id '''

            cr.execute(query, args_list)
            # end of custom code
           
            # original code
            # query = '''SELECT l.id
            #         FROM account_move_line AS l, account_account, account_move am
            #         WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
            #             AND (am.state IN %s)
            #             AND (account_account.internal_type IN %s)
            #             AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
            #             AND ''' + dates_query + '''
            #         AND (l.date <= %s)
            #         AND l.company_id IN %s'''
            # cr.execute(query, args_list)
            # end of custom code

            partners_amount = {}
            aml_ids = cr.fetchall()
            aml_ids = aml_ids and [x[0] for x in aml_ids] or []
            for line in self.env['account.move.line'].browse(aml_ids):
                partner_id = line.partner_id.id or False
                if partner_id not in partners_amount:
                    partners_amount[partner_id] = 0.0
                line_amount = line.balance
                if line.balance == 0:
                    continue
                for partial_line in line.matched_debit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount += partial_line.amount
                for partial_line in line.matched_credit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount -= partial_line.amount

                if not self.env.user.company_id.currency_id.is_zero(line_amount):
                    partners_amount[partner_id] += line_amount
                    lines[partner_id].append({
                        'line': line,
                        'amount': line_amount,
                        'period': i + 1,
                        })
            history.append(partners_amount)
        for partner in partners:
            if partner['partner_id'] is None:
                partner['partner_id'] = False
            if partner['account_id'] is None:
                partner['account_id'] = False
            at_least_one_amount = False
            values = {}
            undue_amt = 0.0
            if partner['partner_id'] in undue_amounts:  # Making sure this partner actually was found by the query
                undue_amt = undue_amounts[partner['partner_id']]

            total[6] = total[6] + undue_amt
            values['direction'] = undue_amt
            if not float_is_zero(values['direction'], precision_rounding=self.env.user.company_id.currency_id.rounding):
                at_least_one_amount = True
            for i in range(5):
                during = False
                if partner['partner_id'] in history[i]:
                    during = [history[i][partner['partner_id']]]
                # Adding counter
                total[(i)] = total[(i)] + (during and during[0] or 0)
                values[str(i)] = during and during[0] or 0.0
                if not float_is_zero(values[str(i)], precision_rounding=self.env.user.company_id.currency_id.rounding):
                    at_least_one_amount = True
            values['total'] = sum([values['direction']] + [values[str(i)] for i in range(5)])
            ## Add for total
            total[(i + 1)] += values['total']
            values['partner_id'] = partner['partner_id']
            if partner['partner_id']:
                browsed_partner = self.env['res.partner'].browse(partner['partner_id'])
                values['name'] = browsed_partner.name and len(browsed_partner.name) >= 45 and browsed_partner.name[0:40] + '...' or browsed_partner.name
                values['trust'] = browsed_partner.trust
            else:
                values['name'] = _('Unknown Partner')
                values['trust'] = False

            values['account_id'] = partner['account_id']
            if partner['account_id']:
                browsed_account = self.env['account.account'].browse(partner['account_id'])
                values['account_name'] = browsed_account.name and len(browsed_account.name) >= 45 and browsed_account.name[0:40] + '...' or browsed_account.name
            else:
                values['account_name'] = _('Unknown Account')

            if at_least_one_amount or (self._context.get('include_nullified_amount') and lines[partner['partner_id']]):
                res.append(values)

        return res, total, lines

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        total = []
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))

        target_move = data['form'].get('target_move', 'all')
        date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))

        if data['form']['result_selection'] == 'customer':
            account_type = ['receivable']
        elif data['form']['result_selection'] == 'supplier':
            account_type = ['payable']
        else:
            account_type = ['payable', 'receivable']

        movelines, total, dummy = self._get_partner_move_lines(account_type, date_from, target_move, data['form']['period_length'],
                                                               data['form']['account_id'], data['form']['partner_id'])
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_partner_lines': movelines,
            'get_direction': total,
        }
