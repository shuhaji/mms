from odoo import models, fields, api, _
from odoo.exceptions import UserError


class KeycardType(models.Model):
    _name = 'keycard.type'

    name = fields.Char()
    sub_url = fields.Char(string='Sub URL')


class KeycardEncoder(models.Model):
    _name = 'keycard.encoder'

    name = fields.Char()
    device_host = fields.Char()
    device_port = fields.Char()
    message = fields.Char()
    keycard_type_id = fields.Many2one('keycard.type', string='Keycard Type')
    company_id = fields.Many2one('res.company',
                                 'Company',
                                 help="Company Id",
                                 required=True,
                                 default=lambda self: self.env.user.company_id.id)
    
