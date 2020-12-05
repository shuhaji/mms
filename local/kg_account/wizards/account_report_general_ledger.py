from odoo import models, api, fields, _
from io import BytesIO
import xlsxwriter
import base64
from datetime import datetime

from odoo.exceptions import UserError


class KGAccountReportGeneralLedger(models.TransientModel):
    _inherit = 'account.report.general.ledger'

    data = fields.Binary('File', readonly=True)
    name = fields.Char('Filename', readonly=True)
    state_position = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    report_type = fields.Selection([('sum', 'Summary'), ('det', 'Details'), ], 'Report Type',
                                   required=True, default='det')

    @api.multi
    def excel_report(self):
        cr = self.env.cr
        fp = BytesIO()

        workbook = xlsxwriter.Workbook(fp)
        workbook.add_format()
        filename = 'General Ledger Report.xlsx'
        worksheet1 = workbook.add_worksheet("General Ledger")

        #################################################################################
        center_title = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'center'})
        center_title.set_font_size('14')
        center_title.set_border()
        #################################################################################
        bold_font = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'left'})
        bold_font.set_text_wrap()
        bold_font_number = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'right'})
        bold_font_number.set_text_wrap()
        #################################################################################
        header_table = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'center'})
        header_table.set_text_wrap()
        header_table.set_bg_color('#eff0f2')
        header_table.set_border()
        #################################################################################
        footer_table = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'right'})
        footer_table.set_text_wrap()
        footer_table.set_border()
        #################################################################################
        set_right = workbook.add_format({'valign': 'vcenter', 'align': 'right'})
        set_right.set_text_wrap()
        set_right.set_border()
        #################################################################################
        set_border = workbook.add_format({'valign': 'vcenter', 'align': 'left'})
        set_border.set_text_wrap()
        set_border.set_border()
        #################################################################################

        footer_format = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'right'})

        worksheet1.set_column('A:A', 20)
        worksheet1.set_column('B:B', 20)
        worksheet1.set_column('C:C', 20)
        worksheet1.set_column('D:D', 20)
        worksheet1.set_column('E:E', 20)
        worksheet1.set_column('F:F', 20)
        worksheet1.set_column('G:G', 20)
        worksheet1.set_column('H:H', 20)
        worksheet1.set_column('I:I', 20)
        worksheet1.set_column('J:J', 20)
        worksheet1.set_column('K:K', 20)
        worksheet1.set_row(0, 30)
        worksheet1.merge_range('A1:K1', 'GENERAL LEDGER', center_title)
        # worksheet1.merge_range('A2:M2', 'PT MAKSINDO', center_title)

        # month_range = calendar.monthrange(int(self.year),self.period)
        # start_date = str(self.year) + '-' + str(self.period).rjust(2,'0') + '-' + str(month_range[0]).rjust(2,'0')
        # end_date = str(self.year) + '-' + str(self.period).rjust(2,'0') + '-' + str(month_range[1]).rjust(2,'0')

        current_user = self.env['res.users'].browse(self.env.context.get('uid', False))
        current_company = current_user.company_id
        start_date = self.date_from
        end_date = self.date_to
        journal_ids = self.journal_ids

        sql_sort = "acc.code, l.date, l.move_id"
        if self.sortby == 'sort_date' and self.report_type == 'sum':
            sql_sort = "acc.code, l.date"
        elif self.sortby == 'sort_journal_partner' and self.report_type == 'sum':
            sql_sort = "acc.code, j.code"
        elif self.sortby == 'sort_journal_partner':
            sql_sort = "acc.code, j.code, p.name, l.move_id"

        where_state = "AND m.state = 'posted' "
        where_display = "AND l.account_id IS NOT NULL "
        having_display = ""
        where_date = ""
        init_balance = False  # self.initial_balance
        # if init_balance and not start_date:
        #     raise UserError(_("You must define a Start Date"))

        if start_date:
            where_date += "AND l.date >= '" + start_date + "' "
            init_date = start_date
        else:
            init_date = '1900-01-01'

        if end_date:
            where_date += "AND l.date <= '" + end_date + "' "

        if self.target_move == 'all':
            where_state = ""

        if self.display_account == 'not_zero':
            having_display = "HAVING SUM(COALESCE(l.debit,0)) > 0 or SUM(COALESCE(l.credit, 0)) > 0 "
        elif self.display_account == 'all':
            where_display = ""
            having_display = ""

        where_journal_id = ""

        if journal_ids:
            codes = [journal.code for journal in
                     self.env['account.journal'].search([('id', 'in', list(journal_ids._ids))])]
            ids = [journal.id for journal in
                   self.env['account.journal'].search([('id', 'in', list(journal_ids._ids))])]
            ids = list(map(str, ids))

            where_journal_id = "AND l.journal_id IN ( " + ', '.join(ids) + " ) "

        worksheet1.write(1, 0, 'Company', bold_font)
        worksheet1.write(1, 1, self.company_id.name, bold_font)

        worksheet1.write(2, 0, 'Period Start', bold_font)
        worksheet1.write(2, 1, start_date, bold_font)
        worksheet1.write(3, 0, 'Period End', bold_font)
        worksheet1.write(3, 1, end_date, bold_font)
        worksheet1.write(4, 0, 'Display Account', bold_font)
        worksheet1.write(4, 1, dict(self._fields['display_account'].selection).get(self.display_account), bold_font)
        worksheet1.write(5, 0, 'Journals', bold_font)
        worksheet1.write(5, 1, ', '.join(codes), bold_font)

        worksheet1.write(2, 9, 'Printed Date', bold_font)
        worksheet1.write(2, 10, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), bold_font)
        worksheet1.write(3, 9, 'Printed By', bold_font)
        worksheet1.write(3, 10, self.env.user.name, bold_font)
        worksheet1.write(4, 9, 'Target Moves', bold_font)
        worksheet1.write(4, 10, dict(self._fields['target_move'].selection).get(self.target_move), bold_font)
        worksheet1.write(5, 9, 'Sorted By', bold_font)
        worksheet1.write(5, 10, dict(self._fields['sortby'].selection).get(self.sortby), bold_font)

        i = 8

        if self.report_type == 'sum':
            data = self.get_data_sum(cr, current_company, having_display, sql_sort, where_display,
                                     where_journal_id, where_state, where_date, init_date)
        else:
            data = self.get_data(cr, current_company, having_display, sql_sort, where_display,
                                 where_journal_id, where_state, where_date, init_date)

        debit = 0
        credit = 0
        balance = 0
        account_id = 0
        header_row = i
        running_balance = 0
        prev_beg_balance = 0

        if self.report_type == 'sum':
            self.write_excel_sum(account_id, balance, bold_font, bold_font_number, credit, data, debit, header_row, i,
                                 prev_beg_balance, running_balance, start_date, worksheet1)
        else:
            self.write_excel(account_id, balance, bold_font, bold_font_number, credit, data, debit, header_row, i,
                             prev_beg_balance, running_balance, start_date, worksheet1)

        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'data': out, 'name': filename, 'state_position': 'get'})
        ir_model_data = self.env['ir.model.data']
        fp.close()
        form_res = ir_model_data.get_object_reference('kg_account', 'account_report_general_ledger_view')
        form_id = form_res and form_res[1] or False

        return {
            'name': 'General Ledger Report',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.report.general.ledger',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    @staticmethod
    def write_excel(account_id, balance, bold_font, bold_font_number, credit, data, debit, header_row, i,
                    prev_beg_balance, running_balance, start_date, worksheet1):
        for row in data:
            if account_id != row['account_id']:
                running_balance = row.get('beg_balance', 0.0)
                worksheet1.write(i, 0, row['acc_code'] + ' ' + row['acc_name'], bold_font)
                if not start_date:
                    beg_balance = 0
                else:
                    beg_balance = row['beg_balance']
                if account_id == 0:
                    prev_beg_balance = beg_balance
                worksheet1.write(i, 6, beg_balance, bold_font_number)
                worksheet1.write(header_row, 7, debit, bold_font_number)
                worksheet1.write(header_row, 8, credit, bold_font_number)
                worksheet1.write(header_row, 9, balance, bold_font_number)
                worksheet1.write(header_row, 10, prev_beg_balance + debit - credit, bold_font_number)
                worksheet1.write(header_row, 11, prev_beg_balance, bold_font_number)

                account_id = row['account_id']
                prev_beg_balance = beg_balance
                debit = 0
                credit = 0
                header_row = i
                i += 1

                # if init_balance:
                #     worksheet1.write(i, 5, 'Initial Balance')
                #     worksheet1.write(i, 7, row['init_debit'])
                #     worksheet1.write(i, 8, row['init_credit'])
                #     worksheet1.write(i, 9, row['beg_balance'])
                #     i += 1

                worksheet1.write(i, 0, 'Date', bold_font)
                worksheet1.write(i, 1, 'JRNL', bold_font)
                worksheet1.write(i, 2, 'Partner', bold_font)
                worksheet1.write(i, 3, 'Ref', bold_font)
                worksheet1.write(i, 4, 'Source', bold_font)
                worksheet1.write(i, 5, 'Description', bold_font)
                worksheet1.write(i, 6, 'Beg. Balance', bold_font)
                worksheet1.write(i, 7, 'Debit', bold_font)
                worksheet1.write(i, 8, 'Credit', bold_font)
                worksheet1.write(i, 9, 'Net Change', bold_font)
                worksheet1.write(i, 10, 'Ending Balance', bold_font)
                worksheet1.write(i, 11, 'Running Balance', bold_font)
                i += 1

            if row['lid']:
                worksheet1.write(i, 0, row['ldate'])
                worksheet1.write(i, 1, row['lcode'])
                worksheet1.write(i, 2, row['partner_name'])
                worksheet1.write(i, 3, row['lref'])
                worksheet1.write(i, 4, row['move_name'])
                worksheet1.write(i, 5, row['lname'])

                worksheet1.write(i, 7, row['debit'])
                worksheet1.write(i, 8, row['credit'])
                running_balance = running_balance + row['debit'] - row['credit']
                worksheet1.write(i, 10, running_balance)

                debit += row['debit']
                credit += row['credit']
                balance = debit - credit
                # beg_balance = row['beg_balance']
                i += 1
        worksheet1.write(header_row, 7, debit, bold_font_number)
        worksheet1.write(header_row, 8, credit, bold_font_number)
        worksheet1.write(header_row, 9, balance, bold_font_number)
        worksheet1.write(header_row, 10, prev_beg_balance + balance, bold_font_number)

    @staticmethod
    def write_excel_sum(account_id, balance, bold_font, bold_font_number, credit, data, debit, header_row, i,
                        prev_beg_balance, running_balance, start_date, worksheet1):
        for row in data:
            if account_id != row['account_id']:
                running_balance = row.get('beg_balance', 0.0)
                worksheet1.write(i, 0, row['acc_code'] + ' ' + row['acc_name'], bold_font)
                if not start_date:
                    beg_balance = 0
                else:
                    beg_balance = row['beg_balance']
                if account_id == 0:
                    prev_beg_balance = beg_balance
                worksheet1.write(i, 2, beg_balance, bold_font_number)
                worksheet1.write(header_row, 3, debit, bold_font_number)
                worksheet1.write(header_row, 4, credit, bold_font_number)
                worksheet1.write(header_row, 5, balance, bold_font_number)
                worksheet1.write(header_row, 6, prev_beg_balance + debit - credit, bold_font_number)
                worksheet1.write(header_row, 7, prev_beg_balance, bold_font_number)

                account_id = row['account_id']
                prev_beg_balance = beg_balance
                debit = 0
                credit = 0
                header_row = i
                i += 1

                # if init_balance:
                #     worksheet1.write(i, 5, 'Initial Balance')
                #     worksheet1.write(i, 7, row['init_debit'])
                #     worksheet1.write(i, 8, row['init_credit'])
                #     worksheet1.write(i, 9, row['beg_balance'])
                #     i += 1

                worksheet1.write(i, 0, 'Date', bold_font)
                worksheet1.write(i, 1, 'JRNL', bold_font)
                worksheet1.write(i, 2, 'Beg. Balance', bold_font)
                worksheet1.write(i, 3, 'Debit', bold_font)
                worksheet1.write(i, 4, 'Credit', bold_font)
                worksheet1.write(i, 5, 'Net Change', bold_font)
                worksheet1.write(i, 6, 'Ending Balance', bold_font)
                worksheet1.write(i, 7, 'Running Balance', bold_font)
                i += 1

            if row['ldate']:
                worksheet1.write(i, 0, row['ldate'])
                worksheet1.write(i, 1, row['lcode'])

                worksheet1.write(i, 3, row['debit'])
                worksheet1.write(i, 4, row['credit'])
                running_balance = running_balance + row['debit'] - row['credit']
                worksheet1.write(i, 6, running_balance)

                debit += row['debit']
                credit += row['credit']
                balance = debit - credit
                # beg_balance = row['beg_balance']
                i += 1
        worksheet1.write(header_row, 3, debit, bold_font_number)
        worksheet1.write(header_row, 4, credit, bold_font_number)
        worksheet1.write(header_row, 5, balance, bold_font_number)
        worksheet1.write(header_row, 6, prev_beg_balance + balance, bold_font_number)

    @api.multi
    def get_data(self, cr, current_company, having_display, sql_sort, where_display,
                 where_journal_id, where_state, where_date, init_date):
        query = """
            WITH z_kg_gl_beg_balance AS (
            SELECT l.account_id AS account_id, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS beg_balance, 
                        COALESCE(SUM(l.debit),0) as init_debit, COALESCE(SUM(l.credit), 0) as init_credit
                        FROM account_move_line l
                        JOIN account_move m ON (l.move_id=m.id)                         
                        WHERE l.date < %s
                        AND l.company_id = %s
                        """ + where_state + """ 
                        """ + where_journal_id + """                         
            GROUP BY l.account_id
            )
            
            SELECT l.id AS lid, acc.id AS account_id, acc."name" as acc_name, 
            acc.code as acc_code, l.date AS ldate, j.code AS lcode, l.currency_id, 
            l.amount_currency, l.ref AS lref, l.name AS lname, 
            COALESCE(z.beg_balance,0) AS beg_balance, 
            COALESCE(z.init_debit,0) AS init_debit, 
            COALESCE(z.init_credit,0) AS init_credit, 
            COALESCE(l.debit,0) AS debit, 
            COALESCE(l.credit,0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance,
            m.name AS move_name, c.symbol AS currency_code, p.name AS partner_name
            FROM account_move_line l
            LEFT JOIN account_move m ON (l.move_id=m.id)
            LEFT JOIN res_currency c ON (l.currency_id=c.id)
            LEFT JOIN res_partner p ON (l.partner_id=p.id)
            LEFT JOIN account_journal j ON (l.journal_id=j.id)            
            LEFT JOIN z_kg_gl_beg_balance z on (l.account_id = z.account_id)
            RIGHT JOIN account_account acc ON (l.account_id = acc.id) 
            """ + where_date + """ 
            """ + where_state + """  
            """ + where_journal_id + """ 
            WHERE acc.company_id = %s
            """ + where_display + """
            GROUP BY l.id, acc.id, acc."name", acc.code, l.date, j.code, l.currency_id, 
            l.amount_currency, l.ref, l.name, m.name, 
            c.symbol, p.name, z.beg_balance, z.init_debit, z.init_credit 
            """ + having_display + """ 
            ORDER BY """ + sql_sort + """     
        """
        params = (init_date, current_company.id, current_company.id)
        self._cr.execute(query, params)
        data = cr.dictfetchall()

        return data

    @api.multi
    def get_data_sum(self, cr, current_company, having_display, sql_sort, where_display,
                     where_journal_id, where_state, where_date, init_date):
        query = """
                WITH z_kg_gl_beg_balance AS (
                SELECT l.account_id AS account_id, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS beg_balance, 
                            COALESCE(SUM(l.debit),0) as init_debit, COALESCE(SUM(l.credit), 0) as init_credit
                            FROM account_move_line l
                            JOIN account_move m ON (l.move_id=m.id)                         
                            WHERE l.date < %s
                            AND l.company_id = %s
                            """ + where_state + """ 
                            """ + where_journal_id + """                         
                GROUP BY l.account_id
                )

                SELECT acc.id AS account_id, acc."name" as acc_name, 
                acc.code as acc_code, l.date AS ldate, j.code AS lcode, l.currency_id, 
                l.amount_currency,                
                COALESCE(z.beg_balance,0) AS beg_balance, 
                COALESCE(z.init_debit,0) AS init_debit, 
                COALESCE(z.init_credit,0) AS init_credit, 
                COALESCE(SUM(l.debit),0) AS debit, 
                COALESCE(SUM(l.credit),0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance,                
                c.symbol AS currency_code                
                FROM account_move_line l
                LEFT JOIN account_move m ON (l.move_id=m.id)
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                LEFT JOIN account_journal j ON (l.journal_id=j.id)            
                LEFT JOIN z_kg_gl_beg_balance z on (l.account_id = z.account_id)
                RIGHT JOIN account_account acc ON (l.account_id = acc.id) 
                """ + where_date + """ 
                """ + where_state + """  
                """ + where_journal_id + """ 
                WHERE acc.company_id = %s
                """ + where_display + """
                GROUP BY acc.id, acc."name", acc.code, l.date, j.code, l.currency_id, 
                l.amount_currency,  
                c.symbol, z.beg_balance, z.init_debit, z.init_credit 
                """ + having_display + """ 
                ORDER BY """ + sql_sort + """     
            """
        params = (init_date, current_company.id, current_company.id)
        self._cr.execute(query, params)
        data = cr.dictfetchall()

        return data
