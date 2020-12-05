# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.model
    def _get_default_advance_payment_account_id(self):
        return self.env.user.company_id.advance_payment_account_id

    @api.model
    def _get_default_advance_payment_outgoing_account_id(self):
        return self.env.user.company_id.advance_payment_outgoing_account_id

    @api.model
    def _get_default_advance_payment_journal_id(self):
        return self.env.user.company_id.advance_payment_journal_id

    advance_payment_account_id = fields.Many2one('account.account',
                                                 string='Incoming Advance Payment Account',
                                                 default=_get_default_advance_payment_account_id,
                                                 help=('The account must be reconcilable'))
    advance_payment_outgoing_account_id = fields.Many2one('account.account',
                                                          string='Outgoing Advance Payment Account',
                                                          default=_get_default_advance_payment_outgoing_account_id,
                                                          help=('The account must be reconcilable'))
    advance_payment_journal_id = fields.Many2one('account.journal', 'Advance Payment Journal',
                                                 default=_get_default_advance_payment_journal_id,
                                                 help=("Default advance payment journal "
                                                       "for the current user's company."))

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        if self.advance_payment_account_id:
            self.sudo().env.user.company_id.advance_payment_account_id = self.advance_payment_account_id
        if self.advance_payment_outgoing_account_id:
            self.sudo().env.user.company_id.advance_payment_outgoing_account_id = self.advance_payment_outgoing_account_id
        if self.advance_payment_journal_id:
            self.sudo().env.user.company_id.advance_payment_journal_id = self.advance_payment_journal_id

