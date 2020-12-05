from odoo import api, fields, models, _

class Company(models.Model):

    _inherit = "res.company"

    company_code = fields.Char()

    tax_config_id = fields.Many2one('hr.kg.payroll.tax.configuration', string="Tax Configuration")

    payroll_config_id = fields.Many2one('hr.kg.payroll.configuration', string="Payroll Configuration")