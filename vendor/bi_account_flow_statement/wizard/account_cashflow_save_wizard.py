# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from openerp import api, fields, models, _

class account_cashflow_save_wizard(models.TransientModel):
    _name = "account.cashflow.save.wizard"
    
    name = fields.Char('filename', readonly=True)
    data = fields.Binary('file', readonly=True)
