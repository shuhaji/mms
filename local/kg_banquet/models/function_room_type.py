from odoo import models, fields, api


class FunctionRoomType(models.Model):
    _name = 'banquet.function.room.type'
    _description = "Function Room Type"

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)