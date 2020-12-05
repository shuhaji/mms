
from odoo import fields, models, api


class KGPurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    purchase_type = fields.Many2one('purchase.type', 'Purchase Type', required=True, )
    department_id = fields.Many2one('hr.department', 'Department', default=lambda self: self.env.user.employee_ids.department_id)
    is_admin = fields.Boolean(string="Check Admin", default=False, compute='get_user_group')

    @api.multi
    def get_user_group(self):
        res_user = self.env.user
        if res_user._is_admin() or res_user.has_group('base.group_erp_manager') \
                or res_user.has_group('kg_purchase.group_purchase_request_general_manager'):
            self.is_admin = True
        else:
            self.is_admin = False


class KGPurchaseRequestLine(models.Model):
    _inherit = 'purchase.request.line'

    request_id_purchase_type = fields.Many2one('purchase.type', related='request_id.purchase_type')
