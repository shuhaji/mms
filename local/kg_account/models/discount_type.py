# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, SUPERUSER_ID, _

class KGDiscountType(models.Model):
    _name = 'discount.type'

    name = fields.Char(
        'Name',
        required=True,
    )

    amount = fields.Float(
        'Amount',
        required=True,
    )

    type_discount_use = fields.Selection([('sale', 'Sales'), ('purchase', 'Purchases'), ('none', 'None')],
                                    string='Discount Scope', required=True, default="sale")
