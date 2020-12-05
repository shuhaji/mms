# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, SUPERUSER_ID, _

class KGHrDepartment(models.Model):
    _inherit = 'hr.department'

    allow_pos_expense = fields.Boolean(
        'Allow POS Expense',
        default=False,
    )

    expense_account_id = fields.Many2one(
        'account.account',
        'Expense Account',
    )
