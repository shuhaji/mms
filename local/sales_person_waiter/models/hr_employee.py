# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # sales_person = fields.Boolean('Sales Person')
    waiter = fields.Boolean('Waiter')