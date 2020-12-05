# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, SUPERUSER_ID, _

class KGDepositType(models.Model):
    _name = 'deposit.type'

    name = fields.Char(
        'Name',
        required=True,
    )

    allow_pos = fields.Boolean(
        'Allow POS',
        default=False,
    )
