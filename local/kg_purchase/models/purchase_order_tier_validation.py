
from odoo import api, models


class KGPurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = ['purchase.order', 'tier.validation']
    _state_from = ['draft']
    _state_to = ['purchase']

    @api.model
    def _get_under_validation_exceptions(self):
        res = super(KGPurchaseOrder, self)._get_under_validation_exceptions()
        res.append('route_id')
        return res
