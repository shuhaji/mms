from odoo import api,fields,models,_ 
from odoo.modules import get_module_path
from odoo.exceptions import UserError
from datetime import datetime
import time
from io import BytesIO
import xlsxwriter
import base64
import calendar

MONTHS  = [
            (1,'Januari'),
            (2,'Februari'),
            (3,'Maret'),
            (4,'April'),
            (5,'Mei'),
            (6,'Juni'),
            (7,'Juli'),
            (8,'Agustus'),
            (9,'September'),
            (10,'Oktober'),
            (11,'November'),
            (12,'Desember')
        ]

class KGARMutationWizard(models.TransientModel):
    _name = 'ar.mutation.wizard'

    # period = fields.Selection(MONTHS, string='Period', required=True)
    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    # year = fields.Char('Year', required=True, default='2019')
    company_id = fields.Many2one(comodel_name='res.company',string='Company', required=True, default=lambda self:self.env.user.company_id.id)

    data = fields.Binary('File', readonly=True)
    name = fields.Char('Filename', readonly=True)
    state_position = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')

    @api.multi
    def print_report(self):
        cr = self.env.cr
        fp = BytesIO()
        
        workbook = xlsxwriter.Workbook(fp)
        workbook.add_format()
        filename = 'AR Mutation Report.xlsx'
        worksheet1 = workbook.add_worksheet("AR Mutation")
        

        #################################################################################
        center_title = workbook.add_format({'bold': 1, 'valign':'vcenter', 'align':'center'})
        center_title.set_font_size('14')
        center_title.set_border()
        #################################################################################
        bold_font = workbook.add_format({'bold': 1, 'valign':'vcenter', 'align':'left'})
        bold_font.set_text_wrap()
        #################################################################################
        header_table = workbook.add_format({'bold': 1, 'valign':'vcenter', 'align':'center'})
        header_table.set_text_wrap()
        header_table.set_bg_color('#eff0f2')
        header_table.set_border()
        #################################################################################
        footer_table = workbook.add_format({'bold': 1, 'valign':'vcenter', 'align':'right'})
        footer_table.set_text_wrap()
        footer_table.set_border()
        #################################################################################
        set_right = workbook.add_format({'valign':'vcenter', 'align':'right'})
        set_right.set_text_wrap()
        set_right.set_border()
        #################################################################################
        set_border = workbook.add_format({'valign':'vcenter', 'align':'left'})
        set_border.set_text_wrap()
        set_border.set_border()
        #################################################################################
        
        footer_format = workbook.add_format({'bold': 1, 'valign':'vcenter', 'align':'right'})

        worksheet1.set_column('A:A', 20)
        worksheet1.set_column('B:B', 20)
        worksheet1.set_column('C:C', 20)
        worksheet1.set_column('D:D', 20)
        worksheet1.set_column('E:E', 20)
        worksheet1.set_column('F:F', 20)
        worksheet1.set_column('G:G', 20)
        worksheet1.set_row(0, 30)
        worksheet1.merge_range('A1:G1', 'A/R MUTATION', center_title)
        # worksheet1.merge_range('A2:M2', 'PT MAKSINDO', center_title)

        # month_range = calendar.monthrange(int(self.year),self.period)
        # start_date = str(self.year) + '-' + str(self.period).rjust(2,'0') + '-' + str(month_range[0]).rjust(2,'0')
        # end_date = str(self.year) + '-' + str(self.period).rjust(2,'0') + '-' + str(month_range[1]).rjust(2,'0')

        start_date = self.start_date
        end_date = self.end_date
        company_id = self.company_id

        worksheet1.write(1, 0, 'Company', bold_font)
        worksheet1.write(1, 1, self.company_id.name, bold_font)

        worksheet1.write(2, 0, 'Period Start', bold_font)
        worksheet1.write(2, 1, start_date, bold_font)
        worksheet1.write(3, 0, 'Period End', bold_font)
        worksheet1.write(3, 1, end_date, bold_font)

        worksheet1.write(2, 5, 'Printed Date', bold_font)
        worksheet1.write(2, 6, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), bold_font)
        worksheet1.write(3, 5, 'Printed By', bold_font)
        worksheet1.write(3, 6, self.env.user.name, bold_font)

        worksheet1.write(5, 0, 'CODE', bold_font)
        worksheet1.write(5, 1, 'DESCRIPTION', bold_font)
        worksheet1.write(5, 2, 'BEG. BALANCE', bold_font)
        worksheet1.write(5, 3, 'FOLIO', bold_font)
        worksheet1.write(5, 4, 'PAYMENT', bold_font)
        worksheet1.write(5, 5, 'CORRECTION', bold_font)
        worksheet1.write(5, 6, 'TOTAL', bold_font)

        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        i = 6

        partner_list = []

        # search previous month balance
        bg_balance_ids = self.env['account.invoice'].search([
            ('type', '=', 'out_invoice'),
            ('state', '=', 'open'),
            ('date_invoice', '<', start_date),
            ('company_id', '=', company_id),
            ])

        for inv in bg_balance_ids:
            if inv.partner_id.id not in partner_list:
                partner_list.append(inv.partner_id.id)

        # search new invoice (current period)
        folio_ids = self.env['account.invoice'].search([
            ('type', '=', 'out_invoice'),
            ('state', '=', 'open'),
            ('date_invoice', '>=', start_date),
            ('date_invoice', '<=', end_date),
            ('company_id', '=', company_id),
            ])

        for inv in folio_ids:
            if inv.partner_id.id not in partner_list:
                partner_list.append(inv.partner_id.id)

        # search payment (current period)
        payment_ids = self.env['account.payment'].search([
            # ('payment_type','=','inbound'),
            ('partner_type', '=', 'customer'),
            ('state', 'in', ['posted','sent','reconciled']),
            ('payment_date', '>=', start_date),
            ('payment_date', '<=', end_date),
            ('company_id', '=', company_id),
            ])

        for p in payment_ids:
            if p.partner_id.id not in partner_list:
                partner_list.append(p.partner_id.id)

        #START LOOPING
        total_bg_balance = 0
        total_folio = 0
        total_payment = 0
        total_correction = 0
        total_all = 0

        for p in partner_list:
            partner_code = '-'
            partner_name = 'NO NAME'
            partner_ids = self.env['res.partner'].browse(p)
            if partner_ids:
                partner_name = partner_ids.name
                partner_code = partner_ids.id

            #BEGINNING BALANCE
            lines = bg_balance_ids.filtered(lambda r: r.partner_id.id == p)
            amount_bg_balance = sum(l.residual for l in lines)

            #BEGINNING BALANCE
            lines = folio_ids.filtered(lambda r: r.partner_id.id == p)
            amount_folio = sum(l.amount_total for l in lines)

            #PAYMENT BALANCE
            lines = payment_ids.filtered(lambda r: r.partner_id.id == p)
            amount_payment = sum(l.amount for l in lines)

            worksheet1.write(i, 0, partner_code)
            worksheet1.write(i, 1, partner_name)
            worksheet1.write(i, 2, amount_bg_balance)
            worksheet1.write(i, 3, amount_folio)
            worksheet1.write(i, 4, amount_payment)
            worksheet1.write(i, 5, 0)
            worksheet1.write(i, 6, (amount_bg_balance-amount_folio)+amount_payment)
            i += 1

            total_bg_balance += amount_bg_balance
            total_folio += amount_folio
            total_payment += amount_payment
            total_correction = 0
            total_all = (total_bg_balance-total_folio)+total_payment
        
        i += 1

        worksheet1.write(i, 0, 'GRAND TOTAL', bold_font)
        worksheet1.write(i, 2, total_bg_balance, footer_format)
        worksheet1.write(i, 3, total_folio, footer_format)
        worksheet1.write(i, 4, total_payment, footer_format)
        worksheet1.write(i, 5, total_correction, footer_format)
        worksheet1.write(i, 6, total_all, footer_format)

        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'data':out, 'name': filename, 'state_position': 'get'})
        ir_model_data = self.env['ir.model.data']
        fp.close()
        form_res = ir_model_data.get_object_reference('kg_account', 'ar_mutation_wizard_form_view')
        form_id = form_res and form_res[1] or False
        
        return {
            'name'              : ('AR Mutation Report'),
            'view_type'         : 'form',
            'view_mode'         : 'form',
            'res_model'         : 'ar.mutation.wizard',
            'res_id'            : self.id,
            'view_id'           : False,
            'views'             : [(form_id, 'form')],
            'type'              : 'ir.actions.act_window',
            'target'            : 'current'
        }

    @api.multi
    def print_report_pdf(self):    
        data = {
            # 'period'        : self.period,
            'start_date'    : self.start_date,
            'end_date'      : self.end_date,
            # 'year'          : self.year,
            'company_id'    : self.company_id.id,
        }
        return self.env.ref('kg_account.menu_report_ar_mutation_pdf').report_action([], data=data)


