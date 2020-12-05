# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons.account.models.account_payment import MAP_INVOICE_TYPE_PARTNER_TYPE
from odoo.tools import float_is_zero


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    advance_payment_ids = fields.Many2many('account.payment', 'account_invoice_payment_rel',
                                           'invoice_id', 'payment_id', string='Advance Payments',
                                           domain=[('is_advance_payment', '=', True)],
                                           copy=False, readonly=True)
    has_advance_payment = fields.Boolean(compute='_has_advance_payment',
                                         string='Has advance payment?')

    @api.multi
    def _has_advance_payment(self):
        for invoice in self:
            advance_payment_args = [
                ('company_id', '=', invoice.company_id.id),
                ('is_advance_payment', '=', True),
                ('partner_id', '=', invoice.partner_id.id),
                ('partner_type', '=', MAP_INVOICE_TYPE_PARTNER_TYPE[invoice.type]),
                ('residual', '!=', 0.0),
                ('state', '=', 'posted'),
            ]
            if self.env['account.payment'].search(advance_payment_args):
                invoice.has_advance_payment = True
            else:
                invoice.has_advance_payment = False

    @api.multi
    def _get_advance_payment_amount(self):
        self.ensure_one()
        advance_payment_amount = 0.0

        for payment in self.payment_move_line_ids:
            if not payment.move_id.line_ids.filtered('is_advance_payment_account'):
                continue

            payment_currency_id = False
            if self.type in ('out_invoice', 'in_refund'):
                amount = sum([p.amount for p in payment.matched_debit_ids if p.debit_move_id in self.move_id.line_ids])
                amount_currency = sum([p.amount_currency for p in payment.matched_debit_ids if p.debit_move_id in self.move_id.line_ids])
                if payment.matched_debit_ids:
                    payment_currency_id = all([p.currency_id == payment.matched_debit_ids[0].currency_id for p in payment.matched_debit_ids]) and payment.matched_debit_ids[0].currency_id or False
            elif self.type in ('in_invoice', 'out_refund'):
                amount = sum([p.amount for p in payment.matched_credit_ids if p.credit_move_id in self.move_id.line_ids])
                amount_currency = sum([p.amount_currency for p in payment.matched_credit_ids if p.credit_move_id in self.move_id.line_ids])
                if payment.matched_credit_ids:
                    payment_currency_id = all([p.currency_id == payment.matched_credit_ids[0].currency_id for p in payment.matched_credit_ids]) and payment.matched_credit_ids[0].currency_id or False

            # get the payment value in invoice currency
            if payment_currency_id and payment_currency_id == self.currency_id:
                amount_to_show = amount_currency
            else:
                amount_to_show = payment.company_id.currency_id.with_context(date=payment.date).compute(amount, self.currency_id)
            if float_is_zero(amount_to_show, precision_rounding=self.currency_id.rounding):
                continue

            advance_payment_amount += amount_to_show
        return advance_payment_amount

