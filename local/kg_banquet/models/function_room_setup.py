from odoo import models, fields, api

class FunctionRoomSetup(models.Model):
    _name = 'banquet.function.room.setup'
    # _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Function Room Setup"
    _rec_name = 'room_type_id'

    # code = fields.Char(string='Code', required=True)
    setup_id = fields.Many2one('banquet.function.room')
    room_type_id = fields.Many2one('banquet.function.room.type', 'Room Type')
    min_capacity = fields.Integer(string='Min Capacity')
    max_capacity = fields.Integer(string='Max Capacity')
    setup_time = fields.Integer(string='Setup Time')
    setdown_time = fields.Integer(string='Setdown Time')
    remark = fields.Char(string='Remark')