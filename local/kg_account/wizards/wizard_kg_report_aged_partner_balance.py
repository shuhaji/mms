from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from datetime import datetime
import time


class WizardAgedPartnerLedger(models.TransientModel):
    _inherit = ['wizard.kg.report.base', 'account.aged.trial.balance']
    _name = 'wizard.kg.report.aged.partner.balance'
    _title = "KG Report - Aged Partner Balance"

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
        get_aged_partner_balance = self.get_aged_partner_balance_data()
        self.report_has_logo = False  # sample report has logo

        data = {
            'config': {
                'start_date': self.date_from,
                'period_length': self.period_length,
                'partners': dict(self._fields['result_selection'].selection).get(self.result_selection),
                'target_move': dict(self._fields['target_move'].selection).get(self.target_move),
                'account_id': self.ap_account_id.name,
                'partner_id': self.supplier_id.name,
                'printed_by': self.env.user.name,
                'period_0': self.period_length,
                'period_1': self.period_length + 1,
                'period_2': 2 * self.period_length,
                'period_3': 2 * self.period_length + 1,
                'period_4': 3 * self.period_length,
            },
            'data': get_aged_partner_balance
        }
        return data

    @api.multi
    def get_aged_partner_balance_data(self):
        where_account_clause, where_partner_clause, where_result_selection_clause, where_target_move_clause = self.query_get_clause()

        supplier_format_clause = tuple(self.supplier_id.ids)
        if len(self.supplier_id.ids) == 1:
            supplier_format_clause = (self.supplier_id.ids[0])

        customer_format_clause = tuple(self.customer_id.ids)
        if len(self.customer_id.ids) == 1:
            customer_format_clause = (self.customer_id.ids[0])

        start_date = self.date_from
        period_0 = str(self.period_length)  # 30
        period_1 = str(self.period_length + 1)  # 31
        period_2 = str(2 * self.period_length)  # 60
        period_3 = str(2 * self.period_length + 1)  # 61
        period_4 = str(3 * self.period_length)  # 90

        query = """                   
            select acc.internal_type, coalesce(s.partner_id, 0) as partner_id, coalesce(rp.name, 'Unknown Partner') as partner_name
                , s.account_id, acc.name as account_name                
                , sum(case when ('""" + start_date + """' - s.date) <= """ + period_0 + """ then 
                    (case when acc.internal_type = 'payable' then -1*(s.debit-s.credit) else (s.debit-s.credit) end) else 0 end) as amount1
                , sum(case when ('""" + start_date + """' - s.date) between """ + period_1 + """ and """ + period_2 + """ then 
                    (case when acc.internal_type = 'payable' then -1*(s.debit-s.credit) else (s.debit-s.credit) end) else 0 end) as amount2
                , sum(case when ('""" + start_date + """' - s.date) between """ + period_3 + """ and """ + period_4 + """ then 
                    (case when acc.internal_type = 'payable' then -1*(s.debit-s.credit) else (s.debit-s.credit) end) else 0 end) as amount3
                , sum(case when ('""" + start_date + """' - s.date) > """ + period_4 + """ then 
                    (case when acc.internal_type = 'payable' then -1*(s.debit-s.credit) else (s.debit-s.credit) end) else 0 end) as amount4
            from account_move_line s
                left join account_move m on m.id = s.move_id
                left join account_account acc on acc.id = s.account_id
                left join res_partner rp on rp.id = s.partner_id
            where s.company_id = {company_id}                                        
                """ + where_account_clause + """
                """ + where_partner_clause + """
                """ + where_result_selection_clause + """
                """ + where_target_move_clause + """   
                and s."date" <= '{start_date}'                                                               
            group by acc.internal_type, s.partner_id, rp.name, s.account_id, acc.name
            having sum(debit-credit) != 0
            order by s.account_id , rp.name
            """
        final_query = query.format(company_id=self.company_id.id, start_date=self.date_from,
                                   ap_account_id=self.ap_account_id.id, ar_account_id=self.ar_account_id.id,
                                   supplier_id=supplier_format_clause, customer_id=customer_format_clause)

        self.env.cr.execute(final_query)
        aged_partner_balance = self.env.cr.dictfetchall()

        return aged_partner_balance

    def query_get_clause(self):

        where_account_clause = ""
        where_partner_clause = "and s.partner_id is not null"

        where_target_move_clause = ""
        if self.target_move == 'posted':
            where_target_move_clause = "and m.state = 'posted'"

        where_result_selection_clause = "and acc.internal_type in ('payable', 'receivable')"
        if self.result_selection == 'supplier':
            where_result_selection_clause = "and acc.internal_type = 'payable'"

            if self.ap_account_id:
                where_account_clause = "and s.account_id = {ap_account_id}"

            if self.supplier_id:
                where_partner_clause = "and s.partner_id in {supplier_id}"
                if len(self.supplier_id.ids) == 1:
                    where_partner_clause = "and s.partner_id = {supplier_id}"

        elif self.result_selection == 'customer':
            where_result_selection_clause = "and acc.internal_type = 'receivable'"

            if self.ar_account_id:
                where_account_clause = "and s.account_id = {ar_account_id}"

            if self.customer_id:
                where_partner_clause = "and s.partner_id in {customer_id}"
                if len(self.customer_id.ids) == 1:
                    where_partner_clause = "and s.partner_id = {customer_id}"

        return where_account_clause, where_partner_clause, where_result_selection_clause, where_target_move_clause

    @staticmethod
    def _define_report_name():

        rpt = "/kg_account/static/rpt/AgedPartnerBalance.mrt"

        return rpt

    # @api.multi
    # def _get_data(self):
    #     """ get data from database or any other source
    #
    #     :return: dict or list of dict
    #     """
    #     data = self.get_param()
    #
    #     res, lines = self.get_report_values(data=data)
    #
    #     if len(res['get_direction']) == 0:
    #         res['get_direction'] = [0, 0, 0, 0, 0, 0, 0]
    #
    #     if data['form']['result_selection'] == 'supplier':
    #         return {
    #             "config": {
    #                 "start_date": res['data']['date_from'],
    #                 "period_length": res['data']['period_length'],
    #                 "partners": dict(self._fields['result_selection'].selection).get(self.result_selection),
    #                 "target_move": dict(self._fields['target_move'].selection).get(self.target_move),
    #                 "account_id": data['form']['ap_account_id'],
    #                 "partner_id": data['form']['supplier_id'],
    #             },
    #             "period": {
    #                 "period_1": "Partners",
    #                 "period_2": res['data']['4']['name'],
    #                 "period_3": res['data']['3']['name'],
    #                 "period_4": res['data']['2']['name'],
    #                 "period_5": res['data']['1']['name'],
    #                 "period_6": "Total",
    #             },
    #             "data_total": {
    #                 "total_1": "Account Total",
    #                 "total_2": -1 * (res['get_direction'][4] + res['get_direction'][6]),
    #                 "total_3": -1 * res['get_direction'][3],
    #                 "total_4": -1 * res['get_direction'][2],
    #                 "total_5": -1 * (res['get_direction'][1] + res['get_direction'][0]),
    #                 "total_6": -1 * res['get_direction'][5],
    #             },
    #             "data": lines
    #         }
    #     elif data['form']['result_selection'] == 'customer':
    #         return {
    #             "config": {
    #                 "start_date": res['data']['date_from'],
    #                 "period_length": res['data']['period_length'],
    #                 "partners": dict(self._fields['result_selection'].selection).get(self.result_selection),
    #                 "target_move": dict(self._fields['target_move'].selection).get(self.target_move),
    #                 "account_id": data['form']['ar_account_id'],
    #                 "partner_id": data['form']['customer_id'],
    #             },
    #             "period": {
    #                 "period_1": "Partners",
    #                 "period_2": res['data']['4']['name'],
    #                 "period_3": res['data']['3']['name'],
    #                 "period_4": res['data']['2']['name'],
    #                 "period_5": res['data']['1']['name'],
    #                 "period_6": "Total",
    #             },
    #             "data_total": {
    #                 "total_1": "Account Total",
    #                 "total_2": res['get_direction'][4] + res['get_direction'][6],
    #                 "total_3": res['get_direction'][3],
    #                 "total_4": res['get_direction'][2],
    #                 "total_5": res['get_direction'][1] + res['get_direction'][0],
    #                 "total_6": res['get_direction'][5],
    #             },
    #             "data": lines
    #         }
    #     else:
    #         return {
    #             "config": {
    #                 "start_date": res['data']['date_from'],
    #                 "period_length": res['data']['period_length'],
    #                 "partners": dict(self._fields['result_selection'].selection).get(self.result_selection),
    #                 "target_move": dict(self._fields['target_move'].selection).get(self.target_move),
    #             },
    #             "period": {
    #                 "period_1": "Partners",
    #                 "period_2": res['data']['4']['name'],
    #                 "period_3": res['data']['3']['name'],
    #                 "period_4": res['data']['2']['name'],
    #                 "period_5": res['data']['1']['name'],
    #                 "period_6": "Total",
    #             },
    #             "data_total": {
    #                 "total_1": "Account Total",
    #                 "total_2": res['get_direction'][4] + res['get_direction'][6],
    #                 "total_3": res['get_direction'][3],
    #                 "total_4": res['get_direction'][2],
    #                 "total_5": res['get_direction'][1] + res['get_direction'][0],
    #                 "total_6": res['get_direction'][5],
    #             },
    #             "data": lines
    #         }
    #
    # def get_param(self):
    #     data = {}
    #     res = {}
    #     data['form'] = self.read(['date_from', 'period_length', 'target_move', 'result_selection',
    #                               'ap_account_id', 'supplier_id', 'ar_account_id', 'customer_id'])[0]
    #     used_context = self._build_contexts(data)
    #     data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
    #     period_length = data['form']['period_length']
    #
    #     if period_length <= 0:
    #         raise UserError(_('You must set a period length greater than 0.'))
    #     if not data['form']['date_from']:
    #         raise UserError(_('You must set a start date.'))
    #
    #     start = datetime.strptime(data['form']['date_from'], "%Y-%m-%d")
    #
    #     for i in range(5)[::-1]:
    #         stop = start - relativedelta(days=period_length - 1)
    #
    #         # custom code to set custom period (e.g 0-30, 31-60, 61-90, 120+)
    #         if i == 4:
    #             res[str(i)] = {
    #                 'name': (str((5-(i+1)) * period_length) + '-' + str((5-i) * period_length)),
    #                 'stop': start.strftime('%Y-%m-%d'),
    #                 'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
    #             }
    #         elif i == 1:
    #             res[str(i)] = {
    #                 'name': ('> '+str(3 * period_length)),
    #                 'stop': start.strftime('%Y-%m-%d'),
    #                 'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
    #             }
    #         else:
    #             res[str(i)] = {
    #                 'name': (i in [2, 3] and (str(((5-(i+1)) * period_length)+1) + '-' + str((5-i) * period_length)) or ('> '+str(4 * period_length))),
    #                 'stop': start.strftime('%Y-%m-%d'),
    #                 'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
    #             }
    #
    #         start = stop - relativedelta(days=1)
    #         data['form'].update(res)
    #     return data
    #
    # def _build_contexts(self, data):
    #     result = {}
    #     result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
    #     result['date_from'] = data['form']['date_from'] or False
    #     result['strict_range'] = True if result['date_from'] else False
    #     return result
    #
    # def get_report_values(self, data=None):
    #     # from /local/kg_account/reports/account_partner_ledger.py
    #     target_move = data['form'].get('target_move', 'all')
    #     date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
    #
    #     if data['form']['result_selection'] == 'customer':
    #         account_type = ['receivable']
    #     elif data['form']['result_selection'] == 'supplier':
    #         account_type = ['payable']
    #     else:
    #         account_type = ['payable', 'receivable']
    #
    #     period_length = data['form']['period_length']
    #     account_id = None
    #     partner_id = None
    #     if data['form']['ap_account_id']:
    #         account_id = (data['form']['ap_account_id'][0])
    #         if data['form']['supplier_id']:
    #             partner_id = data['form']['supplier_id']
    #     elif data['form']['ar_account_id']:
    #         account_id = (data['form']['ar_account_id'][0])
    #         if data['form']['customer_id']:
    #             partner_id = data['form']['customer_id']
    #
    #     move_lines, total, dummy = self.env['report.account.report_agedpartnerbalance'].\
    #         _get_partner_move_lines(account_type, date_from, target_move, period_length, account_id, partner_id)
    #
    #     res = {
    #         'data': data['form'],
    #         'time': time,
    #         'get_partner_lines': move_lines,
    #         'get_direction': total,
    #     }
    #     lines = []
    #
    #     for p in res['get_partner_lines']:
    #         if account_type == ['payable']:
    #             lines.append({
    #                 "partner_name": p['name'],
    #                 "account_name": p['account_name'],
    #                 "total_1": -1 * (p['4'] + p['direction']),
    #                 "total_2": -1 * p['3'],
    #                 "total_3": -1 * p['2'],
    #                 "total_4": -1 * (p['1'] + p['0']),
    #                 "total_5": -1 * p['total'],
    #             })
    #         else:
    #             lines.append({
    #                 "partner_name": p['name'],
    #                 "account_name": p['account_name'],
    #                 "total_1": p['4'] + p['direction'],
    #                 "total_2": p['3'],
    #                 "total_3": p['2'],
    #                 "total_4": p['1'] + p['0'],
    #                 "total_5": p['total'],
    #             })
    #
    #     return res, lines


