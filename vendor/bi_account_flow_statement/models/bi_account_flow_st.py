# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import logging

from openerp import models, fields, api

_logger = logging.getLogger(__name__)

try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import xlwt`.')

try:
    import io
except ImportError:
    _logger.debug('Cannot `import io`.')

try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


class ChartfAccount(models.Model):
    _inherit = 'account.account'

    cash_flow_type = fields.Selection([('operating', 'Operating Activities'), ('invest', 'Investing Activities'),
                                       ('finance', 'Financial Activities')], 'Cash Flow Type')
    finance_report = fields.Many2one(
        'account.financial.report',
        string="Cash Flow Financial Report")


class AccountCashFlow(models.TransientModel):
    _name = 'account.cashflow'

    account_report = fields.Many2one('account.financial.report', 'Account Report', required=True,
                                     default=lambda self: self.env['account.financial.report'].search(
                                         [('name', '=', 'Cash Flow Statement')]))
    start_amount = fields.Float('Cash Initial Balance')
    target_moves = fields.Selection([('all_posted', 'All Posted Entries'), ('all', 'All Entries')], 'Target Moves',
                                    default='all_posted')
    display_dt_cr = fields.Boolean('Display Debit Credit Columns')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    company_id = fields.Many2one('res.company', string="Company",
                                 default=lambda self: self.env['res.company']._company_default_get('account.account'))
    cashflow_cal_id = fields.Many2one('account.cash.flow', 'Cashflow')

    @api.multi
    def check_report_cashflow(self):
        data = {}
        data['form'] = self.read(['start_date', 'end_date'])[0]
        return self._print_report(data)

    def _print_report(self, data):
        data['form'].update(self.read(['start_date', 'end_date', 'target_moves'])[0])
        # return self.env['report'].get_action(self, 'bi_account_flow_statement.report_account_cashflow', data=data)
        return self.env.ref('bi_account_flow_statement.action_cash_flow_st').report_action(self, data=data)

    @api.multi
    def make_excel(self, report_data, data):
        workbook = xlwt.Workbook(encoding="utf-8")
        worksheet = workbook.add_sheet("Cash Flow Statement")
        style_title = xlwt.easyxf(
            "font:height 300; font: name Liberation Sans, bold on,color black; align: horiz center")
        style_table_header = xlwt.easyxf(
            "font:height 200; font: name Liberation Sans, bold on,color black; align: horiz center")
        title = "Cash Flow Statement"
        style = xlwt.easyxf("font:height 200; font: name Liberation Sans,color black;")
        worksheet.write_merge(0, 1, 0, 6, title, style=style_title)
        # worksheet.col.width = 1000
        row = 3
        col = 0
        if not data['display_dt_cr']:

            worksheet.write(4, 0, ['Target Moves'], style=style_table_header)
            worksheet.write(4, 2, ['Cash at the beginning of the year'], style=style_table_header)
            worksheet.write(4, 4, ['Start Date'], style=style_table_header)
            worksheet.write(4, 6, ['End Date'], style=style_table_header)
            worksheet.write(5, 0, self.target_moves, style=style)
            worksheet.write(5, 2, self.start_amount, style=style)
            worksheet.write(5, 4, self.start_date, style=style)
            worksheet.write(5, 6, self.end_date, style=style)
            worksheet.write(7, col, ['Name'], style=style_table_header)
            worksheet.write(7, 2, ['Accounting Activity'], style=style_table_header)
            worksheet.write(7, 6, ['Balance'], style=style_table_header)

            receipt_from = 0
            cash_paid = 0
            for a in report_data:
                if a.get('account_activity') == 'operating' and a.get(
                        'account_report') == 'Cash Receipt From - Operation':
                    receipt_from += a.get('amount_cr') - a.get('amount_dt')
                if a.get('account_activity') == 'operating' and a.get('account_report') == 'Cash Paid to - Operation':
                    cash_paid += a.get('amount_cr') - a.get('amount_dt')
            
            worksheet.write(8, 0, 'Operations', style=style_table_header)
            worksheet.write(8, 6, receipt_from + cash_paid, style=style_table_header)
            worksheet.write(9, 0, 'Cash Receipt from- Operations', style=style_table_header)
            cash_recpt = 0
            for a in report_data:
                if a.get('account_activity') == 'operating' and a.get(
                        'account_report') == 'Cash Receipt From - Operation':
                    cash_recpt += a.get('amount_cr') - a.get('amount_dt')
            worksheet.write(9, 6, cash_recpt, style=style_table_header)


            col = 0
            row = 10
            
            for record in report_data:
                if record.get('account_activity') == 'operating':
                    if record.get('account_report') == 'Cash Receipt From - Operation':
                        col = 0
                        row += 1

                        worksheet.write(row, col, record.get('account_id'), style=style)
                        col += 2
                        worksheet.write(row, col, record.get('account_activity_rep'), style=style)
                        col += 1
                        col += 1
                        col += 2
                        
                        worksheet.write(row, col, record.get('amount_cr') - record.get('amount_dt'), style=style)


            row += 1
            worksheet.write(row, 0, 'Cash Paid to- Operations', style=style_table_header)
            cash_recpt = 0
            for a in report_data:
                if a.get('account_activity') == 'operating' and a.get('account_report') == 'Cash Paid to - Operation':
                    cash_recpt += a.get('amount_cr') - a.get('amount_dt')
            worksheet.write(row, 6, cash_recpt, style=style_table_header)
            for a in report_data:
                if a.get('account_activity') == 'operating':
                    if a.get('account_report') == 'Cash Paid to - Operation':
                        row += 1
                        col = 0
                        worksheet.write(row, col, a.get('account_id'), style=style)
                        col += 2
                        worksheet.write(row, col, a.get('account_activity_rep'), style=style)
                        col += 1
                        col += 1
                        col += 2
                        worksheet.write(row, col, a.get('amount_cr') - a.get('amount_dt'), style=style)
            row += 1
            worksheet.write(row, 0, 'Net Cash Flow From Operations', style=style_table_header)
            worksheet.write(row, 6, receipt_from + cash_paid)

            row += 1
            worksheet.write(row, 0, 'Investing Activities', style=style_table_header)
            receipt_from = 0
            cash_paid = 0
            for a in report_data:
                if a.get('account_activity') == 'invest' and a.get('account_report') == 'Cash Receipt From - Investing':
                    receipt_from += a.get('amount_cr') - a.get('amount_dt')
                if a.get('account_activity') == 'invest' and a.get('account_report') == 'Cash Paid to - Investing':
                    cash_paid += a.get('amount_cr') - a.get('amount_dt')

            worksheet.write(row, 6, receipt_from + cash_paid, style=style_table_header)
            row += 1
            worksheet.write(row, 0, 'Cash Receipt from- Investing', style=style_table_header)
            cash_recpt = 0
            for a in report_data:
                if a.get('account_activity') == 'invest' and a.get('account_report') == 'Cash Receipt From - Investing':
                    cash_recpt += a.get('amount_cr') - a.get('amount_dt')

            worksheet.write(row, 6, cash_recpt, style=style_table_header)
            for a in report_data:
                if a.get('account_activity') == 'invest':
                    if a.get('account_report') == 'Cash Receipt From - Investing':
                        row += 1
                        col = 0
                        worksheet.write(row, col, a.get('account_id'), style=style)
                        col += 2
                        worksheet.write(row, col, a.get('account_activity_rep'), style=style)
                        col += 1
                        col += 1
                        col += 2
                        worksheet.write(row, col, a.get('amount_cr') - a.get('amount_dt'), style=style)
            row += 1
            worksheet.write(row, 0, 'Cash Paid to- Investing', style=style_table_header)
            cash_recpt = 0
            for a in report_data:
                if a.get('account_activity') == 'invest' and a.get('account_report') == 'Cash Paid to - Investing':
                    cash_recpt = cash_recpt + a.get('amount_cr') - a.get('amount_dt')
            worksheet.write(row, 6, cash_recpt, style=style_table_header)
            row += 1
            for a in report_data:
                if a.get('account_activity') == 'invest':
                    if a.get('account_report') == 'Cash Paid to - Investing':
                        row += 1
                        col = 0
                        worksheet.write(row, col, a.get('account_id'), style=style)
                        col += 2
                        worksheet.write(row, col, a.get('account_activity_rep'), style=style)
                        col += 1
                        col += 1
                        col += 2
                        worksheet.write(row, col, a.get('amount_cr') - a.get('amount_dt'), style=style)
            row += 1
            worksheet.write(row, 0, 'Net Cash Flow From Investing', style=style_table_header)
            worksheet.write(row, 6, receipt_from + cash_paid, style=style_table_header)
            row += 1

            worksheet.write(row, 0, 'Financing Activities', style=style_table_header)
            receipt_from = 0
            cash_paid = 0
            for a in report_data:
                if a.get('account_activity') == 'finance' and a.get(
                        'account_report') == 'Cash Receipt From - Financing':
                    receipt_from += a.get('amount_cr') - a.get('amount_dt')
                if a.get('account_activity') == 'finance' and a.get('account_report') == 'Cash Paid to - Financing':
                    cash_paid += a.get('amount_cr') - a.get('amount_dt')

            worksheet.write(row, 6, receipt_from + cash_paid, style=style_table_header)
            row += 1
            worksheet.write(row, 0, 'Cash Receipt from- Financing', style=style_table_header)
            cash_recpt = 0
            for a in report_data:
                if a.get('account_activity') == 'finance' and a.get(
                        'account_report') == 'Cash Receipt From - Financing':
                    cash_recpt += a.get('amount_cr') - a.get('amount_dt')

            worksheet.write(row, 6, cash_recpt, style=style_table_header)
            for a in report_data:
                if a.get('account_activity') == 'finance':
                    if a.get('account_report') == 'Cash Receipt From - Financing':
                        row += 1
                        col = 0
                        worksheet.write(row, col, a.get('account_id'), style=style)
                        col += 2
                        worksheet.write(row, col, a.get('account_activity_rep'), style=style)
                        col += 1
                        col += 1
                        col += 2
                        worksheet.write(row, col, a.get('amount_cr') - a.get('amount_dt'), style=style)
            row += 1
            worksheet.write(row, 0, 'Cash Paid to- Financing', style=style_table_header)
            cash_recpt = 0
            for a in report_data:
                if a.get('account_activity') == 'finance' and a.get('account_report') == 'Cash Paid to - Financing':
                    cash_recpt = cash_recpt + a.get('amount_cr') - a.get('amount_dt')
            worksheet.write(row, 6, cash_recpt, style=style_table_header)
            row += 1
            for a in report_data:
                if a.get('account_activity') == 'finance':
                    if a.get('account_report') == 'Cash Paid to - Financing':
                        row += 1
                        col = 0
                        worksheet.write(row, col, a.get('account_id'), style=style)
                        col += 2
                        worksheet.write(row, col, a.get('account_activity_rep'), style=style)
                        col += 1
                        col += 1
                        col += 2
                        worksheet.write(row, col, a.get('amount_cr') - a.get('amount_dt'), style=style)
            row += 1
            worksheet.write(row, 0, 'Net Cash Flow From Financing', style=style_table_header)
            worksheet.write(row, 6, receipt_from + cash_paid, style=style_table_header)
            row += 1

        if data['display_dt_cr']:

            worksheet.write(4, 0, ['Target Moves'], style=style_table_header)
            worksheet.write(4, 2, ['Cash at the beginning of the year'], style=style_table_header)
            worksheet.write(4, 4, ['Start Date'], style=style_table_header)
            worksheet.write(4, 6, ['End Date'], style=style_table_header)
            worksheet.write(5, 0, self.target_moves, style=style)
            worksheet.write(5, 2, self.start_amount, style=style)
            worksheet.write(5, 4, self.start_date, style=style)
            worksheet.write(5, 6, self.end_date, style=style)
            worksheet.write(7, col, ['Name'], style=style_table_header)
            worksheet.write(7, 2, ['Accounting Activity'], style=style_table_header)
            worksheet.write(7, 3, ['Debit'], style=style_table_header)
            worksheet.write(7, 4, ['Credit'], style=style_table_header)
            worksheet.write(7, 6, ['Balance'], style=style_table_header)

            receipt_from = 0
            cash_paid = 0
            for a in report_data:
                if a.get('account_activity') == 'operating' and a.get('account_report') == 'Cash Receipt From - Operation':
                    receipt_from += a.get('amount_cr') - a.get('amount_dt')
                if a.get('account_activity') == 'operating' and a.get('account_report') == 'Cash Paid to - Operation':
                    cash_paid += a.get('amount_cr') - a.get('amount_dt')
            worksheet.write(8, 0, 'Operations', style=style_table_header)
            worksheet.write(8, 6, receipt_from + cash_paid, style=style_table_header)
            worksheet.write(9, 0, 'Cash Receipt from- Operations', style=style_table_header)
            cash_recpt = 0
            for a in report_data:
                if a.get('account_activity') == 'operating' and a.get('account_report') == 'Cash Receipt From - Operation':
                    cash_recpt += a.get('amount_cr') - a.get('amount_dt')
            worksheet.write(9, 6, cash_recpt, style=style_table_header)
            col = 0
            row = 10

            for record in report_data:
                if record.get('account_activity') == 'operating':
                    if record.get('account_report') == 'Cash Receipt From - Operation':
                        col = 0
                        row += 1

                        worksheet.write(row, col, record.get('account_id'), style=style)
                        col += 2
                        worksheet.write(row, col, record.get('account_activity_rep'), style=style)
                        col += 1
                        worksheet.write(row, col, record.get('amount_dt'), style=style)
                        col += 1
                        worksheet.write(row, col, record.get('amount_cr'), style=style)
                        col += 2
                        worksheet.write(row, col, record.get('amount_cr') - record.get('amount_dt'), style=style)
            row+=1
            worksheet.write(row,0,'Cash Paid to- Operations',style=style_table_header)
            cash_recpt = 0
            for a in report_data:
                if a.get('account_activity') == 'operating' and a.get('account_report') == 'Cash Paid to - Operation':
                    cash_recpt += a.get('amount_cr') - a.get('amount_dt')
            worksheet.write(row, 6, cash_recpt , style=style_table_header)
            for a in report_data:
                if a.get('account_activity') == 'operating':
                    if a.get('account_report') == 'Cash Paid to - Operation':
                        row += 1
                        col = 0
                        worksheet.write(row, col, a.get('account_id'), style=style)
                        col += 2
                        worksheet.write(row, col, a.get('account_activity_rep'), style=style)
                        col += 1
                        worksheet.write(row, col, a.get('amount_dt'), style=style)
                        col += 1
                        worksheet.write(row, col, a.get('amount_cr'), style=style)
                        col += 2
                        worksheet.write(row, col, a.get('amount_cr') - a.get('amount_dt'), style=style)
            row+=1
            worksheet.write(row,0,'Net Cash Flow From Operations',style=style_table_header)
            worksheet.write(row,6,receipt_from + cash_paid)

            row+=1
            worksheet.write(row, 0, 'Investing Activities', style=style_table_header)
            receipt_from = 0
            cash_paid = 0
            for a in report_data:
                if a.get('account_activity') == 'invest' and a.get('account_report') == 'Cash Receipt From - Investing':
                    receipt_from += a.get('amount_cr') - a.get('amount_dt')
                if a.get('account_activity') == 'invest' and a.get('account_report') == 'Cash Paid to - Investing':
                    cash_paid += a.get('amount_cr') - a.get('amount_dt')

            worksheet.write(row, 6, receipt_from + cash_paid, style=style_table_header)
            row+=1
            worksheet.write(row, 0, 'Cash Receipt from- Investing', style=style_table_header)
            cash_recpt = 0
            for a in report_data:
                if a.get('account_activity') == 'invest' and a.get('account_report') == 'Cash Receipt From - Investing':
                    cash_recpt += a.get('amount_cr') - a.get('amount_dt')

            worksheet.write(row, 6, cash_recpt, style=style_table_header)
            for a in report_data:
                if a.get('account_activity') == 'invest':
                    if a.get('account_report') == 'Cash Receipt From - Investing':
                        row += 1
                        col = 0
                        worksheet.write(row, col, a.get('account_id'), style=style)
                        col += 2
                        worksheet.write(row, col, a.get('account_activity_rep'), style=style)
                        col += 1
                        worksheet.write(row, col, a.get('amount_dt'), style=style)
                        col += 1
                        worksheet.write(row, col, a.get('amount_cr'), style=style)
                        col += 2
                        worksheet.write(row, col, a.get('amount_cr') - a.get('amount_dt'), style=style)
            row+=1
            worksheet.write(row, 0, 'Cash Paid to- Investing', style=style_table_header)
            cash_recpt = 0
            for a in report_data:
                if a.get('account_activity') == 'invest' and a.get('account_report') == 'Cash Paid to - Investing':
                    
                    cash_recpt = cash_recpt + (a.get('amount_cr') - a.get('amount_dt'))
                    
            worksheet.write(row, 6, cash_recpt, style=style_table_header)
            row+=1
            for a in report_data:
                if a.get('account_activity') == 'invest':
                    if a.get('account_report') == 'Cash Paid to - Investing':
                        row += 1
                        col = 0
                        worksheet.write(row, col, a.get('account_id'), style=style)
                        col += 2
                        worksheet.write(row, col, a.get('account_activity_rep'), style=style)
                        col += 1
                        worksheet.write(row, col, a.get('amount_dt'), style=style)
                        col += 1
                        worksheet.write(row, col, a.get('amount_cr'), style=style)
                        col += 2
                        worksheet.write(row, col, a.get('amount_cr') - a.get('amount_dt'), style=style)
            row+=1
            worksheet.write(row, 0, 'Net Cash Flow From Investing', style=style_table_header)
            worksheet.write(row, 6, receipt_from + cash_paid, style=style_table_header)

            row+=1

            worksheet.write(row, 0, 'Financing Activities', style=style_table_header)
            receipt_from = 0
            cash_paid = 0
            for a in report_data:
                if a.get('account_activity') == 'finance' and a.get('account_report') == 'Cash Receipt From - Financing':
                    receipt_from += a.get('amount_cr') - a.get('amount_dt')
                if a.get('account_activity') == 'finance' and a.get('account_report') == 'Cash Paid to - Financing':
                    cash_paid += a.get('amount_cr') - a.get('amount_dt')

            worksheet.write(row, 6, receipt_from + cash_paid, style=style_table_header)
            row += 1
            worksheet.write(row, 0, 'Cash Receipt from- Financing', style=style_table_header)
            cash_recpt = 0
            for a in report_data:
                if a.get('account_activity') == 'finance' and a.get('account_report') == 'Cash Receipt From - Financing':
                    cash_recpt += a.get('amount_cr') - a.get('amount_dt')

            worksheet.write(row, 6, cash_recpt, style=style_table_header)
            for a in report_data:
                if a.get('account_activity') == 'finance':
                    if a.get('account_report') == 'Cash Receipt From - Financing':
                        row += 1
                        col = 0
                        worksheet.write(row, col, a.get('account_id'), style=style)
                        col += 2
                        worksheet.write(row, col, a.get('account_activity_rep'), style=style)
                        col += 1
                        worksheet.write(row, col, a.get('amount_dt'), style=style)
                        col += 1
                        worksheet.write(row, col, a.get('amount_cr'), style=style)
                        col += 2
                        worksheet.write(row, col, a.get('amount_cr') - a.get('amount_dt'), style=style)
            row += 1
            worksheet.write(row, 0, 'Cash Paid to- Financing', style=style_table_header)
            cash_recpt = 0
            for a in report_data:
                if a.get('account_activity') == 'finance' and a.get('account_report') == 'Cash Paid to - Financing':
                    cash_recpt = cash_recpt + a.get('amount_cr') - a.get('amount_dt')
            worksheet.write(row, 6, cash_recpt, style=style_table_header)
            row += 1
            for a in report_data:
                if a.get('account_activity') == 'finance':
                    if a.get('account_report') == 'Cash Paid to - Financing':
                        row += 1
                        col = 0
                        worksheet.write(row, col, a.get('account_id'), style=style)
                        col += 2
                        worksheet.write(row, col, a.get('account_activity_rep'), style=style)
                        col += 1
                        worksheet.write(row, col, a.get('amount_dt'), style=style)
                        col += 1
                        worksheet.write(row, col, a.get('amount_cr'), style=style)
                        col += 2
                        worksheet.write(row, col, a.get('amount_cr') - a.get('amount_dt'), style=style)
            row += 1
            worksheet.write(row, 0, 'Net Cash Flow From Financing', style=style_table_header)
            worksheet.write(row, 6, receipt_from + cash_paid, style=style_table_header)
            row += 1

            
        fp = io.BytesIO()
        workbook.save(fp)
        wiz_id = self.env['account.cashflow.save.wizard'].create({
            'state': 'get',
            'data': base64.encodestring(fp.getvalue()),
            'name': 'Account Cashflow Statement.xls'
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Account Cashflow Save Form',
            'res_model': 'account.cashflow.save.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': wiz_id.id,
            'target': 'new'
        }

    @api.multi
    def print_excel(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['start_date', 'end_date', 'display_dt_cr', 'target_moves'])[0]
        data.update({'type': 'excel'})
        report_data = self.env['report.bi_account_flow_statement.report_account_cashflow'].button_calculate_rep(
            data['form'])
        return self.make_excel(report_data, data['form'])


class AccountCashFlow1(models.AbstractModel):
    _name = 'report.bi_account_flow_statement.report_account_cashflow'

    @api.multi
    def button_calculate_rep(self, data):
        acc_journal_obj = self.env['account.move.line']
        account_obj = self.env['account.account']

        pos = []
        result1 = {}

        if data['target_moves'] == 'all_posted':
            domain = [('move_id.state', '=', 'posted')]
        else:
            domain = [('move_id.state', 'in', ['draft', 'posted'])]
        if data['start_date'] and data['end_date']:
            domain += [('date', '>=', data['start_date']), ('date', '<=', data['end_date'])]
        move_line_ids = acc_journal_obj.search(domain).ids

        for acc in account_obj.search([]):
            move_line = acc_journal_obj.search([('id', 'in', move_line_ids), ('account_id', '=', acc.id)])
            debit_val = 0.0
            credit_val = 0.0
            for line in move_line:
                debit_val += line.debit
                credit_val += line.credit

            if move_line:
                result1 = {
                    'amount_dt': debit_val,
                    'amount_cr': credit_val,
                    'account_id': acc.name,
                    'account_activity_rep': acc.finance_report.name,
                    'account_activity': acc.cash_flow_type,
                    'account_report': acc.finance_report.name,
                }
                pos.append(result1)

        if pos:
            return pos
        else:
            return {}

    @api.model
    def get_report_values(self, docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        report_lines = self.button_calculate_rep(data.get('form'))
        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'button_calculate_rep': report_lines,
        }
