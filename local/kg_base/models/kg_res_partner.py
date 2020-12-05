# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, SUPERUSER_ID, _


class KGResPartner(models.Model):
    _inherit = 'res.partner'

    allow_use_city_ledger = fields.Boolean(
        'Allow use city ledger',
        default=False,
    )

    pms_company_id = fields.Char(string='PMS Company ID', size=15,)
    pms_contact_id = fields.Char(string='PMS Contact ID', size=15,)

    _sql_constraints = [
        ('contact_comp_unique', 'unique(pms_company_id, pms_contact_id)', 'Contact ID must be unique per Company!'),
    ]
