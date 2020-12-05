# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_advance_payment_account = fields.Boolean(string='Is advance payment?', default=False)

    @api.multi
    def remove_move_reconcile(self):
        if not self:
            return True
        context = dict(self.env.context or {})
        invoice_id = context.get('invoice_id', False)

        result = super(AccountMoveLine, self).remove_move_reconcile()

        advance_payment_move_lines = self.env['account.move.line']
        rec_move_ids = self.env['account.partial.reconcile']

        for account_move_line in self:
            advance_payment_move_lines = account_move_line.move_id.line_ids.filtered('is_advance_payment_account')
            if advance_payment_move_lines:
                for line in advance_payment_move_lines:
                    rec_move_ids += line.matched_debit_ids
                    rec_move_ids += line.matched_credit_ids

        if invoice_id:
            advance_payment_move_line_args = ['|', ('matched_debit_ids', 'in', rec_move_ids.ids),
                                                   ('matched_credit_ids', 'in', rec_move_ids.ids)]
            for line in self.env['account.move.line'].search(advance_payment_move_line_args):
                line.payment_id.write({'invoice_ids': [(3, invoice_id, None)]})

        result = rec_move_ids.unlink() or result
        if advance_payment_move_lines:
            account_move_line.move_id.button_cancel()
            account_move_line.move_id.unlink()
        return result

