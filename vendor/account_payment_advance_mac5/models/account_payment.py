# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    is_advance_payment = fields.Boolean('Advance Payment?', default=False)
    advance_payment_account_id = fields.Many2one('account.account', 'Advance Payment Account')
    residual = fields.Monetary(string='Remaining Amount', compute='_compute_residual',
                               readonly=True, store=True, help="Remaining amount to apply.")

    @api.one
    @api.depends('advance_payment_account_id')
    def _compute_destination_account_id(self):
        super(AccountPayment, self)._compute_destination_account_id()
        if (not self.invoice_ids and self.payment_type != 'transfer'
                and self.is_advance_payment and self.advance_payment_account_id):
            self.destination_account_id = self.advance_payment_account_id.id

    @api.multi
    @api.depends('amount', 'invoice_ids', 'invoice_ids.payment_move_line_ids')
    def _compute_residual(self):
        for payment in self:
            residual = payment.amount
            payment_lines = payment.invoice_ids.mapped('payment_move_line_ids.move_id.line_ids')
            for line in payment_lines.filtered(lambda l: l.payment_id == payment):
                line_currency = line.currency_id or line.company_id.currency_id
                line_currency = line_currency.with_context(date=payment.payment_date)
                if line.currency_id:
                    line_amount = abs(line.amount_currency)
                else:
                    line_amount = abs(line.credit - line.debit)
                if payment.currency_id != line_currency:
                    residual -= line_currency.compute(line_amount, payment.currency_id)
                else:
                    residual -= line_amount
            payment.residual = residual

    @api.onchange('journal_id', 'payment_type')
    def _onchange_journal_payment_type(self):
        company = self.journal_id.company_id
        self.company_id = company.id
        if self.payment_type == 'inbound':
            self.advance_payment_account_id = company.advance_payment_account_id.id
        else:
            self.advance_payment_account_id = company.advance_payment_outgoing_account_id.id

    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        result = super(AccountPayment, self)._onchange_payment_type()
        self.is_advance_payment = self.env.context.get('default_is_advance_payment', False)
        return result

    def _get_counterpart_move_line_vals(self, invoice=False):
        result = super(AccountPayment, self)._get_counterpart_move_line_vals(invoice=invoice)
        if self.is_advance_payment and self.destination_account_id == self.advance_payment_account_id:
            result['is_advance_payment_account'] = True
        else:
            result['is_advance_payment_account'] = False
        return result

