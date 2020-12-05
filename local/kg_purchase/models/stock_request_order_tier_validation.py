
from odoo import api, models


class KGStockRequestOrder(models.Model):
    _name = "stock.request.order"
    _inherit = ['stock.request.order', 'tier.validation']
    _state_from = ['draft']
    _state_to = ['open']

    @api.model
    def _get_under_validation_exceptions(self):
        res = super(KGStockRequestOrder, self)._get_under_validation_exceptions()
        res.append('route_id')
        return res
