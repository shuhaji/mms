# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, SUPERUSER_ID, _


class KGResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    acc_holder_name = fields.Char('Account Holder Name')

