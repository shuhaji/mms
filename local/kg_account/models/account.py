from odoo import models, fields, api, _
from odoo.osv import expression
from odoo.modules import get_module_path


class KgAccountAccount(models.Model):
    _inherit = "account.account"

    cash_flow_group_id = fields.Many2one(
        'account.group',
        # TODO: if needed, add domain filter is_cash_flow_group = True
        string="Group Cash Flow (Cash Flow Report)")
    departement_id = fields.Many2one('hr.department', string="Department")

    @api.onchange('company_id')
    def onchange_company(self):
        if self.departement_id and self.departement_id.company_id.id != self.company_id.id:
            self.departement_id = False
        return {'domain': {'departement_id': [('company_id', '=', self.company_id.id)]}}

# TODO: if needed, add flag is_cash_flow_group
# class KgAccountGroup(models.Model):
#     _inherit = "account.group"
#
#     is_cash_flow_group = fields.Boolean(default=False)
