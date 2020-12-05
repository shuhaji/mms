from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp
from odoo.tools import float_compare


class KGStockRequest(models.Model):
    _inherit = "stock.request"

    product_id = fields.Many2one(
        states={'draft': [('readonly', False)]}, readonly=True,
        domain=[('type', '=', 'product')]
    )
