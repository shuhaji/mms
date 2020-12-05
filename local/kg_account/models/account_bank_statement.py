# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, SUPERUSER_ID, _


class KgAccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    # invoice from pms or others? (if blank == from odoo)
    app_source = fields.Char(default='')
    app_source_info = fields.Char(compute='compute_app_source_info')

    @api.multi
    def compute_app_source_info(self):
        for rec in self:
            rec.app_source_info = 'pos' if rec.pos_session_id else rec.app_source

