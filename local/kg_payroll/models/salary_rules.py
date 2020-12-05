from odoo import api, fields, models, _


class HrSalaryRule(models.Model):
    _inherit = "hr.salary.rule"

    is_taxed = fields.Boolean(string='Taxed')
    tax_class_id = fields.Selection(selection=[('R', 'Regular Income'), ('I', 'Irregular Income')])
    type_id = fields.Selection(selection=[('FIXED', 'Fixed'), ('VAR', 'Var'), ('BPJS', 'BPJS')])
    account_group = fields.Many2one('account.group', 'Account Group')

