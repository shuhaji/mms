from odoo import models, fields, api, _


class ReservationSource(models.Model):
    _name = 'banquet.reservation.source'
    # _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Reservation Source"

    pms_id = fields.Integer("PMS id")
    name = fields.Char("Name")
    active = fields.Boolean("Active", default=1)
