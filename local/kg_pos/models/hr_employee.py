# -*- coding: utf-8 -*-

from odoo import models, fields, api


class KGHrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_salesperson = fields.Boolean(string='Is Salesperson')
