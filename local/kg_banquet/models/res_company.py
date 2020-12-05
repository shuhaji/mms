from odoo import fields, models


class Company(models.Model):
    _inherit = 'res.company'

    banquet_food_product_id = fields.Many2one('product.product')
    banquet_beverage_product_id = fields.Many2one('product.product')
    banquet_other_product_id = fields.Many2one('product.product')
    banquet_residential_product_id = fields.Many2one('product.product')

    hotel_convention = fields.Boolean(string='Hotel and Convention')
