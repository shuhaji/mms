from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    _sql_constraints = [
        ('default_code_unique', 'unique(default_code)',
            'Product default code (internal number) must be unique!'), ]
