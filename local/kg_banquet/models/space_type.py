from odoo import models, fields, api


class SpaceType(models.Model):
    _name = 'banquet.space.type'
    # _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Space Type"

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)