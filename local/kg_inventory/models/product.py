# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductProduct(models.Model):
    _inherit = 'product.product'

    _sql_constraints = [
        ('default_code_uniq', 'unique(default_code)',
            'Item code must be unique for item number!'), ]
