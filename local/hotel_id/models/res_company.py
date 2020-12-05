# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    hotel_id = fields.Char(string='Hotel Id')
    general_manager = fields.Char(string='General Manager')
    accounting_manager = fields.Char(string='Accounting Manager')
    book_keeper = fields.Char(string='BookKeeper')
    general_cashier = fields.Char(string='General Cashier')
    account_receivable = fields.Char(string='Account Receivable')
    account_payable = fields.Char(string='Account Payable')
    cost_control = fields.Char(string='Cost Control')
    purchasing = fields.Char(string='Purchasing')
    store_keeper = fields.Char(string='Store Keeper')
    branch_id_myvalue = fields.Char(string='Branch ID (MyValue)')

