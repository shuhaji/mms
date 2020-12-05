# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, SUPERUSER_ID, _


class KGTaxCategory(models.Model):
    _name = 'tax.category'

    name = fields.Char(
        'Tax Category',
        compute='set_name',
    )

    tax_category = fields.Char(
        'Tax Category',
        required=True,
    )

    tax_code = fields.Char(
        'Tax Code',
        required=True,
    )

    @api.one
    @api.depends('tax_category', 'tax_code')
    def set_name(self):
        for tax in self:
            tax.name = tax.tax_code + ' ' + tax.tax_category
