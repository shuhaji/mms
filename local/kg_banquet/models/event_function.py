from odoo import models, fields, api, _
from odoo.exceptions import UserError


class EventFunction(models.Model):
    _name = 'banquet.event.function'
    # _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Event Function"

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    menu_ids = fields.Many2many('banquet.menu', string='Banquet Menu')
