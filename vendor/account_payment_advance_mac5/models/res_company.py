# -*- coding: utf-8 -*-

from odoo import fields, models


class Company(models.Model):
    _inherit = 'res.company'

    advance_payment_account_id = fields.Many2one('account.account',
                                                 'Incoming Advance Payment Account')
    advance_payment_outgoing_account_id = fields.Many2one('account.account',
                                                          'Outgoing Advance Payment Account')
    advance_payment_journal_id = fields.Many2one('account.journal', 'Default Advance Payment Journal')
