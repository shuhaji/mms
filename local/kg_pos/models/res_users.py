# -*- coding: utf-8 -*-

from odoo import models, fields, api


class KGResUsers(models.Model):
    _inherit = 'res.users'

    allow_void_bill = fields.Boolean(
        string='Allow Void Bill', track_visibility='onchange',
    )

    allow_cancel_item = fields.Boolean(
        string='Allow Cancel Item', track_visibility='onchange',
    )

    allow_payment_access = fields.Boolean(
        string='Allow Payment Access', track_visibility='onchange',
    )

    allow_invoice_access = fields.Boolean(
        string='Allow Invoice Access',
        help='Check this box for user with access to print invoice repeatedly',
    )


    @api.onchange('allow_payment_access', 'allow_cancel_item', 'allow_cancel_item', 'allow_void_bill', 'allow_coupon_create')
    def _default_payment_access(self):
        if self.allow_payment_access is False and self.allow_void_bill is False \
                and self.allow_cancel_item is False and self.allow_coupon_create is False:
            self.pos_security_pin = False
