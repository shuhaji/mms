
from odoo import api, models


class KGTierDefinition(models.Model):
    _inherit = "tier.definition"

    @api.model
    def _get_tier_validation_model_names(self):
        res = super(KGTierDefinition, self)._get_tier_validation_model_names()
        res.append("purchase.order")
        res.append("stock.request.order")
        return res
