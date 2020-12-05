# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from datetime import date, datetime

from odoo.exceptions import UserError, ValidationError


class KGAccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.model
    def create(self, vals):
        self.check_account_period_lock(
            company_id=self.company_id.id, old_date=False, new_date=vals.get('payment_date')
        )
        res = super(KGAccountPayment, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        for rec in self:
            rec.check_account_period_lock(
                company_id=rec.company_id.id, old_date=rec.payment_date, new_date=vals.get('payment_date')
            )
        res = super(KGAccountPayment, self).write(vals)
        return res

    @api.model
    def check_account_period_lock(self, company_id, old_date, new_date):
        # internal transfer masuk ke flag is_ap_closed
        trx_type = "is_ar_closed" if self.partner_type == 'customer' else "is_ap_closed"
        for rec in self:
            if new_date or old_date:
                # validate old date,
                if old_date:
                    rec.env['account.period'].check_lock_period(rec, company_id, old_date, trx_type)
                # Validate new date
                if new_date and new_date != (old_date or False):
                    rec.env['account.period'].check_lock_period(rec, company_id, new_date, trx_type)


