# -*- coding: utf-8 -*-

from odoo import models, fields, api

class KGPickingList(models.Model):
    _name = 'kgpicking.list'
    _rec_name = 'name'

    name = fields.Char("Name")

    partner_id = fields.Many2one(comodel_name="res.partner",
            string="Partner", required=False, )
    route_id = fields.Many2one(comodel_name="stock.location.route",
            string="type work", required=False, )
    warehouse_id = fields.Many2one(comodel_name="stock.warehouse",
            string="warehouse", required=False, )
    company_id = fields.Many2one(comodel_name="res.company",
            string="Customer/vendor", required=False, )
    move_ids = fields.Many2one(comodel_name="stock.move", inverse_name="pickinglist_id",
            string="stock move", required=False, )