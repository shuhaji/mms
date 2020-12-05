from io import StringIO

from odoo import api, fields, models

from dateutil import parser
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.modules import get_module_path
import csv
import json
import base64


class SPTMasaProses(models.Model):
    _name = 'hr.kg.tax.notification'
    _rec_name = 'company_id'

    _sql_constraints = [
        ('company_period_unique', 'unique(date_from,structure_id,company_id)', 'You cannot insert a period date that '
                                                                               'already exist or same structure !'),
    ]

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id.id,
                                 readonly=True,
                                 states={'confirmed': [('readonly', True)]})
    structure_id = fields.Many2one('hr.payroll.structure', string='Salary Structure',max_value=100,
                                   states={'confirmed': [('readonly', True)]})

    def _get_default_percentage(self):
        payroll_config_pph = self.env['hr.kg.payroll.configuration'].search([('company_id', '=',
                                                                              self.env.user.company_id.id)], limit=1)
        return payroll_config_pph.pph_percentage

    percentage = fields.Float('Percentage (%)', required=True, readonly=True, default=_get_default_percentage)
    period = fields.Date(default=fields.Date.today, string="Period", required=True,
                         states={'confirmed': [('readonly', True)]})
    tax_file = fields.Binary('Tax File', compute='generate_tax_file', default=False)
    file_name = fields.Char(default=False)
    tax_object_code = fields.Char(required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed')], default='draft', states={'confirmed': [('readonly', True)]})
    date_from = fields.Date(string='Start Date', compute='filter_date_onchange', store=True,
                            states={'confirmed': [('readonly', True)]})
    date_to = fields.Date(string='End Date', compute='filter_date_onchange', store=True,
                          states={'confirmed': [('readonly', True)]})

    @api.one
    @api.depends('period')
    def filter_date_onchange(self):
        if self.period:
            date_from, date_to = self.set_period(self.period)
            self.update({
                "date_from": date_from,
                "date_to": date_to})

    @api.model
    def set_period(self, period):
        if period:
            date_val = parser.parse(period)
            date_from = date_val.replace(day=1) if date_val else False
            date_to = date_from + relativedelta(months=1, days=-1) if date_from else False
            return date_from, date_to
        else:
            return False, False

    @api.multi
    @api.depends('file_name')
    def generate_tax_file(self):
        file_content = ""
        if self.file_name and self.state == 'confirmed':
            query = """SELECT he.name, he.npwp_no, CAST(hp.brutto AS INTEGER ) as brutto_paid, 
            CAST(hp.pph21_paid AS INTEGER ) FROM hr_payslip hp  LEFT JOIN hr_employee he ON hp.employee_id = he.id
            WHERE  hp.company_id = {company_id} AND (hp.date_from >= '{date_from}' AND hp.date_to <= '{date_to}') AND
            hp.state='done'"""
            query += " AND hp.struct_id = {structure_id}".format(structure_id=self.structure_id.id) \
                if self.structure_id.id else ''
            final_query = query.format(percentage=self.percentage, company_id=self.company_id.id,
                                       date_from=self.date_from,
                                       date_to=self.date_to)
            self.env.cr.execute(final_query)
            cs = self.env.cr.dictfetchall()

            stream_out = StringIO()
            stream_out.write("Masa Pajak;Tahun Pajak;Pembetulan;NPWP;Nama;Kode Pajak;Jumlah Bruto;Jumlah PPH;Kode Negara\n")
            for row in cs:
                stream_out.write("{MasaPajak};{TahunPajak};{Pembetulan};{NPWP};{Nama};{KodePajak};{JumlahBruto};"
                                 "{JumlahPPH};{KodeNegara}".
                                 format(MasaPajak=self.period[5:7], TahunPajak=self.period[0:4], Pembetulan=0,
                                        NPWP=row.get('npwp_no') or '000000000000000', Nama=row.get('name') or '',
                                        KodePajak=self.tax_object_code or '', JumlahBruto=row.get('brutto_paid') or '',
                                        JumlahPPH=row.get('pph21_paid') or '', KodeNegara=""))
                stream_out.write("\n")
            file_content = stream_out.getvalue()

        self.update({'tax_file': base64.b64encode(bytes(file_content, "utf-8"))})

    @api.multi
    def button_confirm(self):
        if self.state == 'draft' or self.tax_object_code is None:
            self.file_name = "tax_file-{comp_id}-{period}.csv".format(
                comp_id=self.company_id.id,
                period=self.period[0:7]
            )
            self.state = 'confirmed'
            query = """UPDATE hr_payslip SET pph21_paid = pph21_amount * '{percentage}' / 100
                        WHERE company_id = '{company_id}' AND (date_from >= '{date_from}' 
                        AND date_to <= '{date_to}') AND state ='done'"""
            query += " AND struct_id = {structure_id}".format(structure_id=self.structure_id.id) \
                if self.structure_id.id else ''
            final_query = query.format(percentage=self.percentage, company_id=self.company_id.id,
                                       date_from=self.date_from,
                                       date_to=self.date_to)
            self.env.cr.execute(final_query)
        else:
            raise UserError('Please check SPT Masa state or Fill the blank of Tax Object Code')
