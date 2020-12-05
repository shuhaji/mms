# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons.account.models.account_payment import MAP_INVOICE_TYPE_PARTNER_TYPE
from odoo.exceptions import UserError, ValidationError


class AccountAdvancePaymentInvoice(models.TransientModel):
    _name = 'account.advance.payment.invoice'
    _description = 'Apply Advance Payments'

    journal_id = fields.Many2one('account.journal', string='Application Journal', required=True)
    date = fields.Date(string='Application Date', required=True, default=fields.Date.context_today)
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')])
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    invoice_residual = fields.Monetary(string='Total Invoice Balances',
                                       currency_field='currency_id', readonly=True)
    advance_payment_total = fields.Monetary(compute='_get_advance_payment_total',
                                            string='Total Advance Payments',
                                            currency_field='currency_id')
    advance_payment_residual = fields.Monetary(compute='_get_advance_payment_total',
                                               string='Remaining Advance Payments',
                                               currency_field='currency_id')
    advance_payment_ids = fields.Many2many('account.payment', 'account_advance_payment_invoice_rel',
                                           'advance_payment_invoice_id', 'payment_id',
                                           'Advance Payments', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)

    @api.multi
    @api.depends('advance_payment_ids')
    def _get_advance_payment_total(self):
        for record in self:
            payment_residual = 0.0
            for payment in record.advance_payment_ids:
                payment_currency = payment.currency_id.with_context(date=payment.payment_date)
                if record.currency_id != payment_currency:
                    payment_residual += payment_currency.compute(payment.residual,
                                                                 record.currency_id)
                else:
                    payment_residual += payment.residual
            record.advance_payment_total = payment_residual
            record.advance_payment_residual = (payment_residual > record.invoice_residual
                                               and payment_residual - record.invoice_residual
                                               or 0.0)

    @api.onchange('company_id')
    def _onchange_company(self):
        self.journal_id = self.company_id.advance_payment_journal_id.id

    @api.model
    def default_get(self, fields):
        rec = super(AccountAdvancePaymentInvoice, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')

        # Checks on context parameters
        if not active_model or not active_ids:
            raise UserError(_("Programmation error: wizard action executed without active_model or active_ids in context."))
        if active_model != 'account.invoice':
            raise UserError(_("Programmation error: the expected model for this action is 'account.invoice'. The provided one is '%d'.") % active_model)

        # Checks on received invoice records
        invoices = self.env[active_model].browse(active_ids)
        if any(invoice.state != 'open' for invoice in invoices):
            raise UserError(_("You can only apply advance payments for open invoices"))
        if any(inv.partner_id != invoices[0].partner_id for inv in invoices):
            raise UserError(_("In order to pay multiple invoices at once, invoices should have the same partner."))
        if any(inv.account_id != invoices[0].account_id for inv in invoices):
            raise UserError(_("In order to pay multiple invoices at once, invoices should have the same account."))
        if any(MAP_INVOICE_TYPE_PARTNER_TYPE[inv.type] != MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type] for inv in invoices):
            raise UserError(_("You cannot mix customer invoices and vendor bills in a single payment."))
        if any(inv.currency_id != invoices[0].currency_id for inv in invoices):
            raise UserError(_("In order to pay multiple invoices at once, they must use the same currency."))

        rec.update({
            'company_id': invoices[0].company_id.id,
            'currency_id': invoices[0].currency_id.id,
            'invoice_residual': sum(inv.residual for inv in invoices),
            'partner_id': invoices[0].partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type]
        })
        return rec

    @api.multi
    def apply_advance_payment(self):
        for record in self:
            if (record.advance_payment_total > record.invoice_residual
                    and len(record.advance_payment_ids) > 1):
                error = ('Multiple application of advance payments that '
                         'exceed the invoice balance is not yet supported')
                raise ValidationError(_(error))

            partner_id = self.env['res.partner']._find_accounting_partner(record.partner_id).id
            invoices = self.env['account.invoice'].browse(self._context.get('active_ids'))
            invoice_move_lines = invoices.mapped('move_id').mapped('line_ids')
            invoice_move_lines = invoice_move_lines.filtered(lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable'))

            advance_payment_accounts = self.env['account.account']
            payment_move_line = {}
            for payment in record.advance_payment_ids:
                payment_account = payment.advance_payment_account_id
                advance_payment_accounts |= payment_account
                if payment.id not in payment_move_line:
                    payment_move_line[payment.id] = self.env['account.move.line']
                payment_move_line[payment.id] |= payment.move_line_ids.filtered(lambda r: not r.reconciled and r.account_id == payment_account)
                payment.write({'invoice_ids': [(4, x.id, None) for x in invoices]})

            advance_payment_move_lines = []
            advance_payment_residual = record.advance_payment_total - record.advance_payment_residual
            counterpart_balance = currency_exchange_diff = 0.0
            currency_company = record.company_id.currency_id
            payment_move_lines = self.env['account.move.line']

            for lines in payment_move_line.values():
                payment_move_lines |= lines
                for line in lines:
                    balance = abs(line.balance)
                    currency = line.currency_id or currency_company
                    currency_invoice = record.currency_id
                    payment_date = line.payment_id.payment_date

                    if currency_company != currency_invoice:
                        advance_payment_residual = currency_invoice.with_context(date=payment_date)\
                                                       .compute(advance_payment_residual,
                                                                currency_company)

                    balance_now = balance_used = min(balance, advance_payment_residual)
                    if currency != currency_company and balance:
                        if line.amount_currency:
                            amount_currency = abs(line.amount_currency * (balance_used / balance))
                        else:
                            amount_currency = balance_used
                        balance_now = currency.compute(amount_currency, currency_company)

                    if currency != currency_invoice:
                        balance_now = currency.with_context(date=payment_date).compute(balance_now,
                                                                                   currency_invoice)
                        balance_now = currency_invoice.compute(balance_now, currency)

                    counterpart_balance += balance_now
                    currency_exchange_diff += balance_now - balance_used

                    if record.partner_type == 'customer':
                        credit = 0.0
                        debit = balance_used
                        advance_payment_residual -= debit
                    else:
                        debit = 0.0
                        credit = balance_used
                        advance_payment_residual -= credit

                    currency_company = currency_company.with_context(date=payment_date)
                    if currency_company != currency_invoice:
                        advance_payment_residual = currency_company.compute(advance_payment_residual,
                                                                            currency_invoice)

                    if credit or debit:
                        advance_payment_move_lines.append((0, 0, {
                            'name': 'Advance Payment: %s' % ', '.join(lines.mapped('move_id').mapped('name')),
                            'account_id': line.account_id.id,
                            'partner_id': partner_id,
                            'debit': debit,
                            'credit': credit,
                            'payment_id': line.payment_id.id,
                            'is_advance_payment_account': True,
                        }))

            if counterpart_balance:
                advance_payment_move_lines.append((0, 0, {
                    'name': 'Advance Payment: %s' % ', '.join(invoices.mapped('number')),
                    'account_id': invoices[0].account_id.id,
                    'partner_id': partner_id,
                    'debit': record.partner_type == 'supplier' and counterpart_balance or 0.0,
                    'credit': record.partner_type == 'customer' and counterpart_balance or 0.0,
                    'is_advance_payment_account': False,
                }))

            if currency_exchange_diff:
                currency_exchange_journal = record.company_id.currency_exchange_journal_id
                if currency_exchange_diff < 0:
                    if record.partner_type == 'supplier':
                        currency_exchange_account = currency_exchange_journal.default_debit_account_id
                        credit = 0.0
                        debit = abs(currency_exchange_diff)
                    else:
                        currency_exchange_account = currency_exchange_journal.default_credit_account_id
                        credit = abs(currency_exchange_diff)
                        debit = 0.0
                else:
                    if record.partner_type == 'supplier':
                        currency_exchange_account = currency_exchange_journal.default_credit_account_id
                        credit = currency_exchange_diff
                        debit = 0.0
                    else:
                        currency_exchange_account = currency_exchange_journal.default_debit_account_id
                        credit = 0.0
                        debit = currency_exchange_diff

                advance_payment_move_lines.append((0, 0, {
                    'name': 'Currency Exchange Difference',
                    'account_id': currency_exchange_account.id,
                    'partner_id': partner_id,
                    'debit': debit,
                    'credit': credit,
                    'is_advance_payment_account': False,
                }))

            if advance_payment_move_lines:
                name = record.journal_id.with_context(ir_sequence_date=record.date).sequence_id.next_by_id()
                move = self.env['account.move'].create({
                    'name': name,
                    'date': record.date,
                    'company_id': record.company_id.id,
                    'journal_id': record.journal_id.id,
                    'line_ids': advance_payment_move_lines,
                })
                move.post()

                invoice_payment_move_lines = move.line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable'))
                advance_payment_move_lines = move.line_ids.filtered(lambda r: not r.reconciled and r.account_id in advance_payment_accounts)

                (invoice_payment_move_lines + invoice_move_lines).reconcile()
                (advance_payment_move_lines + payment_move_lines).reconcile()
