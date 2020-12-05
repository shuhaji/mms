from odoo import models, fields, api, _


class KGBanquetRateType(models.Model):
    _name = 'banquet.rate.type'
    # _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Rate Type"

    pms_id = fields.Char(string='PMS Id', required=True)
    name = fields.Char(string='Name', required=True)
    active = fields.Boolean(string='Active', default=1)
