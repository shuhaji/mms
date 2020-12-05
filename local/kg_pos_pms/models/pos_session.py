# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from addons.point_of_sale.models.pos_session import PosSession
from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
import datetime
import time


class KGPOSSessionPMS(models.Model):
    _inherit = 'pos.session'

    working_date = fields.Date(string='Working Date', required=True,
                            index=True, copy=False, default=fields.Date.context_today,
                            help="Active Working Date")

    @api.model
    def create(self, values):
        res = super(KGPOSSessionPMS, self).create(values)
        response = self.env['pos.helpers'].get_system_date_from_pms()
        if response and response.get('SystemDate'):
            pms_date = response.get('SystemDate')
            res.working_date = str(pms_date)
        for statement in res.statement_ids:
            statement.date = res.working_date
        return res