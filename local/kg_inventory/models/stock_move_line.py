# -*- coding: utf-8 -*-

from odoo import models, fields, api

class KGMoveLine(models.Model):
    _name = 'stock.move'
    _inherit = 'stock.move'

    pickinglist_id = fields.One2many(comodel_name="picking.list", string="Picking List" , required=False, )
