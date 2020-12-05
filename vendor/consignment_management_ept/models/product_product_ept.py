from odoo import models, fields, api, _


class product_product_ept(models.Model):
    _inherit = 'product.product'

    is_consignment_product = fields.Boolean('Can be Sold for Consignment', default=True)
