# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, SUPERUSER_ID, _


class KGIssuerType(models.Model):
    _name = 'kg.issuer.type'

    name = fields.Char(
        'Issuer Type',
        required=True,
    )
