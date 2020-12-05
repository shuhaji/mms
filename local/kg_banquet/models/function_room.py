from odoo import models, fields, api


class FunctionRoom(models.Model):
    _name = 'banquet.function.room'
    _inherit = ['mail.thread']
    _description = "Function Room"

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    space_type_id = fields.Many2one('banquet.space.type',
                                    'Space Type', required=True)
    company_id = fields.Many2one(comodel_name='res.company',string='Company',
                                 required=True, default=lambda self: self.env.user.company_id.id)
    room_setup_ids = fields.One2many('banquet.function.room.setup', 'setup_id')
    min_capacity = fields.Integer(string='Min Capacity')
    max_capacity = fields.Integer(string='Max Capacity')
    area = fields.Integer(string='Area (Square Meter)', compute='calc_area')
    width = fields.Integer(string='Width')
    length = fields.Integer(string='Length')
    price_per_meter = fields.Integer(string='Price per square meter')
    price_total = fields.Integer(string='Price Total', compute='calc_price_total')
    taxes_ids = fields.Many2many('account.tax', 'function_room_taxes_rel', 'room_id', 'account_tax_id',
                                string="Taxes")
    join_ids = fields.Many2many('banquet.function.room',
                                'function_room_joined_rel', 'function_room_id', 'joined_id',
                                string="Select Room",
                                domain="['&',('joined','=',False),('not_combineable','=',False)]")
    shareable_room = fields.Boolean(string='Is Shareable Room')
    floor_loading = fields.Boolean(string='Is Floor Loading')
    light_dimmable = fields.Boolean(string='Is Light Dimmable')
    have_speaker = fields.Boolean(string='Is Have Speaker')
    not_combineable = fields.Boolean(string='Is Not Combineable')
    joined = fields.Boolean(string="Join Room")
    internal_phone_number = fields.Char(string='Internal Phone Number')
    remark = fields.Text(string='Remark')

    @api.onchange('width', 'length')
    def calc_area(self):
        if self.width:
            self.area = self.width * self.length
        if self.length:
            self.area = self.width * self.length

    @api.onchange('area', 'price_per_meter')
    def calc_price_total(self):
        if self.area:
            self.price_total = self.area * self.price_per_meter
        if self.length:
            self.price_total = self.area * self.price_per_meter
