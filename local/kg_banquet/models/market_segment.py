from odoo import models, fields, api, _


class MarketSegment(models.Model):
    _name = 'banquet.market.segment'
    # _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Market Segment"

    code = fields.Char(string='Market Code')
    name = fields.Char(string='Market Name')
