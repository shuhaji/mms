# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from addons.point_of_sale.models.pos_session import PosSession
from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
import datetime
import time


class KGPOSSession(models.Model):
    _inherit = 'pos.session'

    @api.model
    def create(self, vals):
        self.check_account_period_lock(
            company_id=self.config_id.company_id.id, old_date=False,
            new_date=vals.get('working_date', vals.get('start_at'))
        )
        res = super(KGPOSSession, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        for rec in self:
            rec.check_account_period_lock(
                company_id=rec.config_id.company_id.id,
                old_date=getattr(rec, 'working_date', rec.start_at),
                new_date=vals.get('working_date', vals.get('start_at')))
        res = super(KGPOSSession, self).write(vals)
        return res

    @api.model
    def check_account_period_lock(self, company_id, old_date, new_date):
        for rec in self:
            if new_date or old_date:
                # validate old date,
                if old_date:
                    rec.env['account.period'].check_lock_period_pos(rec, company_id, old_date)
                # Validate new date
                if new_date and new_date != (old_date or False):
                    rec.env['account.period'].check_lock_period_pos(rec, company_id, new_date)
