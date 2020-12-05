# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, pycompat
from odoo.tools import float_compare, float_round, float_repr
from odoo.tools.misc import formatLang, format_date

import time
import math


class KGAccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    @api.model
    def create(self, vals):
        self.check_account_period_lock(
            pos_statement_id=vals.get('pos_statement_id', self.pos_statement_id),
            company_id=self.company_id.id, old_date=False, new_date=vals.get('date')
        )
        res = super(KGAccountBankStatementLine, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        for rec in self:
            rec.check_account_period_lock(
                pos_statement_id=vals.get('pos_statement_id', rec.pos_statement_id),
                company_id=rec.company_id.id, old_date=rec.date, new_date=vals.get('date')
            )
        res = super(KGAccountBankStatementLine, self).write(vals)
        return res

    @api.model
    def check_account_period_lock(self, pos_statement_id, company_id, old_date, new_date):
        if pos_statement_id:
            # bank statement from POS Session, by pass,
            # already checked in POS Session create/write
            return
        else:
            trx_type = "is_bank_statement_closed"
            for rec in self:
                if new_date or old_date:
                    # validate old date,
                    if old_date:
                        rec.env['account.period'].check_lock_period(rec, company_id, old_date, trx_type)
                    # Validate new date
                    if new_date and new_date != (old_date or False):
                        rec.env['account.period'].check_lock_period(rec, company_id, new_date, trx_type)
