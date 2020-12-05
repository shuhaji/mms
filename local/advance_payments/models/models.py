# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError
from dateutil import parser
from lxml import etree


class AdvancePayments(models.Model):
    _inherit = 'account.payment'

    # state = fields.Selection([
    #     ('draft', 'Draft'),
    #     ('posted', 'Posted'),
    #     ('sent', 'Sent'),
    #     ('reconciled', 'Reconciled'),
    #     ('cancelled', 'Cancelled')], readonly=True, default='draft', copy=False, string="Status")

    posting_date = fields.Datetime('Apply To Room Date')  # apply to room date
    status_deposit = fields.Selection([
        ('NEW', 'New'),
        ('CONFIRMED', 'Confirmed'),
        ('POSTED', 'Applied To Room'),
        ('CLOSED', 'Closed'),
        ('REFUND', 'Refund')], default='NEW', copy=False)
    guest_name = fields.Char()
    remark = fields.Text()
    reff_no = fields.Char()
    reservation_no = fields.Char('Room ReservationNo')
    close_date = fields.Datetime('Close Date')
    room_no = fields.Char()
    # Credit Info for settlement/funding
    # card number only store the first 4 digit and the last 4 digit -- for checking later on
    #  ex: 1234-XXXX-XXXX-3456
    card_number = fields.Char(
        'Card Number',
    )
    card_holder_name = fields.Char(
        'Card Holder Name',
    )
    issuer_type_id = fields.Many2one(
        'kg.issuer.type',
        'Issuer Type',
    )

    @api.multi
    def post(self):
        super(AdvancePayments, self).post()
        for rec in self:
            if rec.is_advance_payment and rec.status_deposit == 'NEW':
                rec.write({'status_deposit': 'CONFIRMED'})
        return True

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        res = super(AdvancePayments, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        if view_type != 'search' and self.env.uid != SUPERUSER_ID \
                and (res['name'] == 'kg.advance.payments.tree' or res['name'] == 'view.account.payment.advance.customer.form'):
            # Check if user is in group that allow creation
            has_hide_create_button_group = self.env.user.has_group('advance_payments.group_hide_add_advance_deposit')
            if has_hide_create_button_group:
                root = etree.fromstring(res['arch'])
                root.set('create', 'false')
                res['arch'] = etree.tostring(root)

        return res

    @api.multi
    def apply_to_room(self, params):
        for adv_deposit in self:
            if not adv_deposit.is_advance_payment:
                raise UserError(
                    _("You can only apply an advance payment/deposit, not normal payment."))
            company = adv_deposit.journal_id.company_id
            if not company.guest_ledger_account_id.id:
                raise UserError(_('Guest Ledger not defined on the company.'))
            if adv_deposit.status_deposit == 'POSTED':
                raise UserError("Advance Deposit with PMS ID " +
                                adv_deposit.communication + " already Applied/Posted To Room")
            if adv_deposit.status_deposit not in ('NEW', 'CONFIRMED'):
                raise UserError(_('[Status Deposit] is not NEW/CONFIRMED'))
            required_fields = ""
            if not adv_deposit.posting_date and not params.get('posting_date'):
                required_fields = "Apply To Room Date"
            if not adv_deposit.room_no and not params.get('room_no'):
                required_fields = required_fields + ", " if required_fields else ""
                required_fields += "Room No"
            if not adv_deposit.reservation_no and not params.get('reservation_no'):
                required_fields = required_fields + ", " if required_fields else ""
                required_fields += "Reservation No"
            if required_fields:
                raise UserError('{required_fields} is required'.format(required_fields=required_fields))

            adv_deposit.room_no = params.get('room_no', adv_deposit.room_no)
            adv_deposit.posting_date = params.get('posting_date', adv_deposit.posting_date)
            adv_deposit.reservation_no = params.get('reservation_no', adv_deposit.reservation_no)
            adv_deposit.status_deposit = 'POSTED'
            amount = adv_deposit.residual
            adv_deposit.residual = 0
            apply_move_lines = list()
            # Prepare line Debit GAD
            apply_move_lines.append((0, 0, {
                'name': '(AD) Apply To Room ' + (adv_deposit.name or ''),
                'account_id': adv_deposit.advance_payment_account_id.id,
                'partner_id': adv_deposit.partner_id.id,
                'payment_id': adv_deposit.id,
                'debit': amount,
                'credit': 0,
                'is_advance_payment_account': True,
            }))
            # Prepare line Credit Guest Ledger
            apply_move_lines.append((0, 0, {
                'name': '(AD) Apply To Room ' + (adv_deposit.name or ''),
                'account_id': company.guest_ledger_account_id.id,
                'partner_id': adv_deposit.partner_id.id,
                'payment_id': adv_deposit.id,
                'debit': 0,
                'credit': amount,
                'is_advance_payment_account': False,
            }))
            # Create journal entry
            apply_date = fields.Date.from_string(adv_deposit.posting_date)
            name = adv_deposit.journal_id.with_context(
                ir_sequence_date=fields.Date.to_string(apply_date)).sequence_id.next_by_id()
            move = self.env['account.move'].create({
                'name': name + '/ADATR',
                'date': apply_date,
                'company_id': adv_deposit.company_id.id,
                'journal_id': adv_deposit.journal_id.id,
                'line_ids': apply_move_lines,
            })
            move.post()
            return {"status": "OK", "message": "Advance Deposit applied to room successfully"}

    is_allow_to_close = fields.Boolean("Allow to Close", compute="get_is_allow_to_close")

    @api.multi
    def get_is_allow_to_close(self):
        for rec in self:
            if rec.residual == 0:
                return False
            else:
                return True

    @api.multi
    def close_deposit(self, params=None):
        for adv_deposit in self:
            # validate date from params
            param_close_date = params.get('close_date') if params else ""
            try:
                if param_close_date:
                    close_date = parser.parse(param_close_date)
                    close_date = fields.Date.to_string(close_date)
                else:
                    # default, get current user date
                    close_date = fields.Date.context_today(self)
            except Exception as ex:
                raise UserError('Close date ' + param_close_date +
                                ' is not in a valid format (expect in yyyy-mm-dd)')
            if not adv_deposit.is_advance_payment:
                raise UserError(
                    _("You can only close an advance payment/deposit, not normal payment."))
            company = adv_deposit.journal_id.company_id
            if not company.close_advance_deposit_account_id.id:
                raise UserError(_('Close Advance Deposit Account not defined on the company.'))
            if adv_deposit.status_deposit not in ('CONFIRMED', ):
                raise UserError(_('[Status Deposit] is not CONFIRMED'))
            amount = adv_deposit.residual
            if amount <= 0:
                raise UserError(_('Failed to Close, Remaining Amount is 0!'))

            adv_deposit.status_deposit = 'CLOSED'
            adv_deposit.residual = 0
            apply_move_lines = list()
            # Prepare line Debit GAD
            apply_move_lines.append((0, 0, {
                'name': 'Close Adv. Deposit: ' + adv_deposit.name,
                'account_id': adv_deposit.advance_payment_account_id.id,
                'partner_id': adv_deposit.partner_id.id,
                'payment_id': adv_deposit.id,
                'debit': amount,
                'credit': 0,
                'is_advance_payment_account': True,
            }))
            # Prepare line Credit Guest Ledger
            apply_move_lines.append((0, 0, {
                'name': 'Close Adv. Deposit: ' + adv_deposit.name,
                'account_id': company.close_advance_deposit_account_id.id,
                'partner_id': adv_deposit.partner_id.id,
                'payment_id': adv_deposit.id,
                'debit': 0,
                'credit': amount,
                'is_advance_payment_account': False,
            }))
            # Create journal entry
            adv_deposit.close_date = close_date
            name = adv_deposit.journal_id.with_context(
                ir_sequence_date=close_date).sequence_id.next_by_id()
            move = self.env['account.move'].create({
                'name': name,
                'date': close_date,
                'company_id': adv_deposit.company_id.id,
                'journal_id': adv_deposit.journal_id.id,
                'line_ids': apply_move_lines,
            })
            move.post()
            return {"status": "OK", "message": "Advance Deposit closed successfully"}

    @api.model
    def get_default_journal_account_id(self):
        return self.journal_id.default_debit_account_id.id if self.payment_type in ('outbound', 'transfer') \
            else self.journal_id.default_credit_account_id.id

    @api.multi
    @api.depends('amount', 'invoice_ids', 'invoice_ids.payment_move_line_ids')
    def _compute_residual(self):
        # fixed bug residual amount is minus for payment not advance payment!
        for payment in self:
            residual = payment.amount + payment.writeoff_amount
            payment_lines = payment.invoice_ids.mapped('payment_move_line_ids.move_id.line_ids')
            if payment.is_advance_payment:
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
            else:
                # not advance payment, check from account_partial_reconcile
                payment_account_id = payment.get_default_journal_account_id()
                amount_paid = 0
                move_lines = payment_lines.filtered(
                    lambda l: l.account_id.id != payment_account_id)
                for line in move_lines:
                    for match_payment in line.matched_debit_ids:
                        amount_paid += match_payment.amount
                residual -= amount_paid

            payment.residual = residual
