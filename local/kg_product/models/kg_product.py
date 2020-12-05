# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, SUPERUSER_ID, _


class KGProduct(models.Model):
    _inherit = 'product.template'

    def _default_tax_category(self):
        return self.env['tax.category'].search([('tax_code', '=', 'ATM')], limit=1).id

    tax_category_id = fields.Many2one(
        'tax.category',
        'Tax Category',
        default=_default_tax_category
    )

    main_category = fields.Char(related='categ_id.main_parent', store=False)

    allow_open_price = fields.Boolean('Allow Open Price')

    allow_custom_item = fields.Boolean('Allow Custom Item')

    is_banquet = fields.Boolean('Is Banquet')

    item_type = fields.Selection([
        ('fnb', 'Food & Beverage'),
        ('eqp', 'Equipment'),
        ('svc', 'Service'),
    ], 'Item Type')

    responsible_department = fields.Many2one('hr.department', string='Responsible Department')
    additional_tax_id = fields.Many2one('account.tax', string='Additional Tax', ondelete='restrict', domain=[('type_tax_use', '=', 'sale')])

    is_consignment = fields.Boolean('Is Consignment')
    consignment_product_owner = fields.Many2one('res.partner', string='Product Owner', domain=[('supplier', '=', True)])
    consignment_purchase_cost = fields.Float(string='Consignment Price')
