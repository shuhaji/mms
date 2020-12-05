# -*- coding: utf-8 -*-

from odoo import models, fields, api

class KGStockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = 'stock.picking'

