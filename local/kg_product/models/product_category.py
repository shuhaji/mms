# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductCategory(models.Model):
    _inherit = 'product.category'

    main_parent = fields.Char(compute='_main_parent_category', store=True)
    expense_account_group = fields.Many2one('account.group', help='Account Group for Expense')

    @api.multi
    @api.depends('parent_id')
    def _main_parent_category(self):
        for record in self:
            record.main_parent = record.get_parent()

    def get_parent(self):
        if self.parent_id:
            parent = self.parent_id.get_parent()
        else:
            parent = self.name.upper() if self.name else ""
        return parent
