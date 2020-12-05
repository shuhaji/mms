# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, SUPERUSER_ID, _

class KGHrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_officer_check = fields.Boolean(
        'Is officer check',
        default=False,
    )

    expense_account_id = fields.Many2one(
        'account.account',
        'Expense Account',
    )
