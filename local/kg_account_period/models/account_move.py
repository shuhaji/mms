# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError


class KGAccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def _check_lock_date(self):
        for move in self:
            move.env['account.period'].check_lock_period_account_move(self, move)
        super(KGAccountMove, self)._check_lock_date()

