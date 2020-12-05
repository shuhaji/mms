from odoo import models, fields, api, _


class RoomType(models.Model):
    _name = 'banquet.room.type'
    # _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Room Type"

    pms_id = fields.Char("PMS id")
    name = fields.Char("Name")
    active = fields.Boolean("Active", default=1)
