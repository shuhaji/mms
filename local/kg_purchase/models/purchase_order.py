
from odoo import fields, models, api
from odoo.exceptions import UserError


class KGPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    purchase_type = fields.Many2one('purchase.type', 'Purchase Type', required=True, )
    from_purchase_request = fields.Boolean(default=False)

    @api.multi
    def button_approve(self, force=False):
        for order in self:
            for lines in order.order_line:
                if lines.price_unit <= 0 or lines.product_qty <= 0:
                    raise UserError("Product Qty and Unit Price for Purchase Order cannot be less or equal to 0")
        res = super(KGPurchaseOrder, self).button_approve()
        return res


class KGPurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    purchase_request_name = fields.Char(related='purchase_request_lines.request_id.name')
