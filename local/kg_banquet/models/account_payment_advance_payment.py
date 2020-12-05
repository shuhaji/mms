# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ReservationAdvancePayment(models.Model):
    _inherit = 'account.payment'

    bqt_reservation_id = fields.Many2one('banquet.reservation', string='BQT Reservation Id', ondelete='set null')
