from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, pycompat

import time


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    shift = fields.Char(string='Shift', related='pos_session_id.shift_id.code')
    reference = fields.Char('Reference', compute='get_name_shift')

    @api.multi
    def get_name_shift(self):
        for data in self:
            if data.shift:
                name_shift = data.name + '/' + (data.shift or '')
            else:
                name_shift = data.name

            data.reference = name_shift

    @api.multi
    def button_confirm_bank_kg_dept_officer(self):
        self._balance_check()
        statements = self.filtered(lambda r: r.state == 'open')
        for statement in statements:
            moves = self.env['account.move']
            for st_line in statement.line_ids:
                if st_line.account_id and not st_line.journal_entry_ids.ids:
                    st_line.fast_counterpart_creation()
                elif not st_line.journal_entry_ids.ids and not statement.currency_id.is_zero(st_line.amount):
                    raise UserError(
                        _('All the account entries lines must be processed in order to close the statement.'))

                for aml in st_line.journal_entry_ids:
                    moves |= aml.move_id
            if moves:
                moves.filtered(lambda m: m.state != 'posted').post()
            statement.message_post(body=_('Statement %s confirmed, journal items were created.') % (statement.name,))
        statements.link_bank_to_partner()
        statements.write({'state': 'confirm', 'date_done': time.strftime("%Y-%m-%d %H:%M:%S")})


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    card_number = fields.Char(
        'Card Number',
    )

    card_holder_name = fields.Char(
        'Card Holder Name',
    )

    # tidak perlu, krn bisa bisa diambil dari journal id (journal = bank EDC Credit card)
    # issuer_bank_id = fields.Many2one(
    #     'account.journal',
    #     'Issuer Bank',
    # )

    issuer_type_id = fields.Many2one(
        'kg.issuer.type',
        'Issuer Type',
    )

    voucher_id = fields.Many2one(
        'kg.voucher',
        'Applied Voucher',
    )

    voucher_no = fields.Char(
        'Voucher Number',
    )

    def process_reconciliation(self, counterpart_aml_dicts=None, payment_aml_rec=None, new_aml_dicts=None):
        """ Match statement lines with existing payments (eg. checks) and/or payables/receivables (eg. invoices and credit notes) and/or new move lines (eg. write-offs).
            If any new journal item needs to be created (via new_aml_dicts or counterpart_aml_dicts), a new journal entry will be created and will contain those
            items, as well as a journal item for the bank statement line.
            Finally, mark the statement line as reconciled by putting the matched moves ids in the column journal_entry_ids.

            :param self: browse collection of records that are supposed to have no accounting entries already linked.
            :param (list of dicts) counterpart_aml_dicts: move lines to create to reconcile with existing payables/receivables.
                The expected keys are :
                - 'name'
                - 'debit'
                - 'credit'
                - 'move_line'
                    # The move line to reconcile (partially if specified debit/credit is lower than move line's credit/debit)

            :param (list of recordsets) payment_aml_rec: recordset move lines representing existing payments (which are already fully reconciled)

            :param (list of dicts) new_aml_dicts: move lines to create. The expected keys are :
                - 'name'
                - 'debit'
                - 'credit'
                - 'account_id'
                - (optional) 'tax_ids'
                - (optional) Other account.move.line fields like analytic_account_id or analytics_id

            :returns: The journal entries with which the transaction was matched. If there was at least an entry in counterpart_aml_dicts or new_aml_dicts, this list contains
                the move created by the reconciliation, containing entries for the statement.line (1), the counterpart move lines (0..*) and the new move lines (0..*).
        """
        counterpart_aml_dicts = counterpart_aml_dicts or []
        payment_aml_rec = payment_aml_rec or self.env['account.move.line']
        new_aml_dicts = new_aml_dicts or []

        aml_obj = self.env['account.move.line']

        company_currency = self.journal_id.company_id.currency_id
        statement_currency = self.journal_id.currency_id or company_currency
        st_line_currency = self.currency_id or statement_currency

        counterpart_moves = self.env['account.move']

        # Check and prepare received data
        if any(rec.statement_id for rec in payment_aml_rec):
            raise UserError(_('A selected move line was already reconciled.'))
        for aml_dict in counterpart_aml_dicts:
            if aml_dict['move_line'].reconciled:
                raise UserError(_('A selected move line was already reconciled.'))
            if isinstance(aml_dict['move_line'], pycompat.integer_types):
                aml_dict['move_line'] = aml_obj.browse(aml_dict['move_line'])
        for aml_dict in (counterpart_aml_dicts + new_aml_dicts):
            if aml_dict.get('tax_ids') and isinstance(aml_dict['tax_ids'][0], pycompat.integer_types):
                # Transform the value in the format required for One2many and Many2many fields
                aml_dict['tax_ids'] = [(4, id, None) for id in aml_dict['tax_ids']]
        if any(line.journal_entry_ids for line in self):
            raise UserError(_('A selected statement line was already reconciled with an account move.'))

        # Fully reconciled moves are just linked to the bank statement
        total = self.amount

        for aml_rec in payment_aml_rec:
            total -= aml_rec.debit - aml_rec.credit
            aml_rec.with_context(check_move_validity=False).write({'statement_line_id': self.id})
            counterpart_moves = (counterpart_moves | aml_rec.move_id)

        # Create move line(s). Either matching an existing journal entry (eg. invoice), in which
        # case we reconcile the existing and the new move lines together, or being a write-off.
        if counterpart_aml_dicts or new_aml_dicts:
            st_line_currency = self.currency_id or statement_currency
            st_line_currency_rate = self.currency_id and (self.amount_currency / self.amount) or False

            # Create the move
            self.sequence = self.statement_id.line_ids.ids.index(self.id) + 1
            move_vals = self._prepare_reconciliation_move(self.statement_id.name)
            move = self.env['account.move'].create(move_vals)
            counterpart_moves = (counterpart_moves | move)

            # Create The payment
            payment = self.env['account.payment']
            if abs(total) > 0.00001:
                partner_id = self.partner_id and self.partner_id.id or False
                partner_type = False
                if partner_id:
                    if total < 0:
                        partner_type = 'supplier'
                    else:
                        partner_type = 'customer'

                payment_methods = (
                                              total > 0) and self.journal_id.inbound_payment_method_ids or self.journal_id.outbound_payment_method_ids
                currency = self.journal_id.currency_id or self.company_id.currency_id

                payment = self.env['account.payment'].create({
                    'payment_method_id': payment_methods and payment_methods[0].id or False,
                    'payment_type': total > 0 and 'inbound' or 'outbound',
                    'partner_id': self.partner_id and self.partner_id.id or False,
                    'partner_type': partner_type,
                    'journal_id': self.statement_id.journal_id.id,
                    'payment_date': self.date,
                    'state': 'reconciled',
                    'currency_id': currency.id,
                    'amount': abs(total),
                    'communication': self._get_communication(payment_methods[0] if payment_methods else False),
                    'name': self.statement_id.name or _("Bank Statement %s") % self.date,
                })

            # Complete dicts to create both counterpart move lines and write-offs
            to_create = (counterpart_aml_dicts + new_aml_dicts)
            ctx = dict(self._context, date=self.date)
            for aml_dict in to_create:
                aml_dict['move_id'] = move.id
                aml_dict['partner_id'] = self.partner_id.id
                aml_dict['statement_line_id'] = self.id
                if st_line_currency.id != company_currency.id:
                    aml_dict['amount_currency'] = aml_dict['debit'] - aml_dict['credit']
                    aml_dict['currency_id'] = st_line_currency.id
                    if self.currency_id and statement_currency.id == company_currency.id and st_line_currency_rate:
                        # Statement is in company currency but the transaction is in foreign currency
                        aml_dict['debit'] = company_currency.round(aml_dict['debit'] / st_line_currency_rate)
                        aml_dict['credit'] = company_currency.round(aml_dict['credit'] / st_line_currency_rate)
                    elif self.currency_id and st_line_currency_rate:
                        # Statement is in foreign currency and the transaction is in another one
                        aml_dict['debit'] = statement_currency.with_context(ctx).compute(
                            aml_dict['debit'] / st_line_currency_rate, company_currency)
                        aml_dict['credit'] = statement_currency.with_context(ctx).compute(
                            aml_dict['credit'] / st_line_currency_rate, company_currency)
                    else:
                        # Statement is in foreign currency and no extra currency is given for the transaction
                        aml_dict['debit'] = st_line_currency.with_context(ctx).compute(aml_dict['debit'],
                                                                                       company_currency)
                        aml_dict['credit'] = st_line_currency.with_context(ctx).compute(aml_dict['credit'],
                                                                                        company_currency)
                elif statement_currency.id != company_currency.id:
                    # Statement is in foreign currency but the transaction is in company currency
                    prorata_factor = (aml_dict['debit'] - aml_dict['credit']) / self.amount_currency
                    aml_dict['amount_currency'] = prorata_factor * self.amount
                    aml_dict['currency_id'] = statement_currency.id

            # Create write-offs
            # When we register a payment on an invoice, the write-off line contains the amount
            # currency if all related invoices have the same currency. We apply the same logic in
            # the manual reconciliation.
            counterpart_aml = self.env['account.move.line']
            for aml_dict in counterpart_aml_dicts:
                counterpart_aml |= aml_dict.get('move_line', self.env['account.move.line'])
            new_aml_currency = False
            if counterpart_aml \
                    and len(counterpart_aml.mapped('currency_id')) == 1 \
                    and counterpart_aml[0].currency_id \
                    and counterpart_aml[0].currency_id != company_currency:
                new_aml_currency = counterpart_aml[0].currency_id
            for aml_dict in new_aml_dicts:
                aml_dict['payment_id'] = payment and payment.id or False
                if new_aml_currency and not aml_dict.get('currency_id'):
                    aml_dict['currency_id'] = new_aml_currency.id
                    aml_dict['amount_currency'] = company_currency.with_context(ctx).compute(
                        aml_dict['debit'] - aml_dict['credit'], new_aml_currency)

                # custom code by mario ardi
                if self.env.context.get('order_with_same_journal_id'):
                    order_with_same_journal_id = self.env.context.get('order_with_same_journal_id')
                    department_account = order_with_same_journal_id.filtered(
                        lambda order: (order.name in aml_dict['name'])).mapped('department_id').mapped(
                        'expense_account_id')
                    employee_account = order_with_same_journal_id.filtered(
                        lambda order: (order.name in aml_dict['name'])).mapped('employee_id').mapped(
                        'expense_account_id')

                    if department_account or employee_account:
                        amount_cogs = 0
                        for ord_line in order_with_same_journal_id:
                            for order_line2 in ord_line.lines:
                                amount_cogs += order_line2.product_id.standard_price * order_line2.qty

                        aml_dict['credit'] = amount_cogs

                aml_obj.with_context(check_move_validity=False, apply_taxes=True).create(aml_dict)

            # Create counterpart move lines and reconcile them
            for aml_dict in counterpart_aml_dicts:
                if aml_dict['move_line'].partner_id.id:
                    aml_dict['partner_id'] = aml_dict['move_line'].partner_id.id
                aml_dict['account_id'] = aml_dict['move_line'].account_id.id
                aml_dict['payment_id'] = payment and payment.id or False

                counterpart_move_line = aml_dict.pop('move_line')
                if counterpart_move_line.currency_id and counterpart_move_line.currency_id != company_currency and not aml_dict.get(
                        'currency_id'):
                    aml_dict['currency_id'] = counterpart_move_line.currency_id.id
                    aml_dict['amount_currency'] = company_currency.with_context(ctx).compute(
                        aml_dict['debit'] - aml_dict['credit'], counterpart_move_line.currency_id)

                new_aml = aml_obj.with_context(check_move_validity=False).create(aml_dict)
                (new_aml | counterpart_move_line).reconcile()

            # Balance the move
            st_line_amount = -sum([x.balance for x in move.line_ids])
            aml_dict = self._prepare_reconciliation_move_line(move, st_line_amount)
            aml_dict['payment_id'] = payment and payment.id or False

            # custom code by andi
            # TODO: cek custom code ini, apakah bisa mengambil departement_id/employee_id
            #       langsung dari self.pos_statement_id.departement_id / .employee_id?
            #   dan apakah bisa langsung dg mengoverrde dan menaruh code ini
            #       di dalam: self._prepare_reconciliation_move_line() daripada di sini.
            if self.env.context.get('order_with_same_journal_id'):
                order_with_same_journal_id = self.env.context.get('order_with_same_journal_id')

                department_account = order_with_same_journal_id.filtered(
                    lambda order:
                    (
                            order.name in aml_dict['name']
                    )
                ).mapped('department_id').mapped('expense_account_id')

                employee_account = order_with_same_journal_id.filtered(
                    lambda order:
                    (
                            order.name in aml_dict['name']
                    )
                ).mapped('employee_id').mapped('expense_account_id')

                if department_account:
                    amount_cogs = 0
                    for ord_line in order_with_same_journal_id:
                        for order_line2 in ord_line.lines:
                            amount_cogs += order_line2.product_id.standard_price * order_line2.qty

                    aml_dict['account_id'] = department_account.id or False
                    aml_dict['debit'] = amount_cogs

                if employee_account:
                    aml_dict['account_id'] = employee_account.id or False
                    aml_dict['debit'] = amount_cogs

            # end of custom code

            aml_obj.with_context(check_move_validity=False).create(aml_dict)

            # custom code to change journal date
            if self.env.context.get('start_date', False):
                move.write({
                    'date': self.env.context.get('start_date', False),
                })
                for line in move.line_ids:
                    line.write({
                        # 'date_maturity': self.env.context.get('start_date', False)
                        'date': self.env.context.get('start_date', False)
                    })
            # end of custom code

            move.post()
            # record the move name on the statement line to be able to retrieve it in case of unreconciliation
            self.write({'move_name': move.name})

            # custom code by aan: check if bank statement from pos, add flag app_source = 'pos' on account.payment
            app_source = ''
            if payment and hasattr(self, 'pos_statement_id') and self.pos_statement_id:
                app_source = 'pos'
            # end of custom code
            # original code
            payment and payment.write({
                'payment_reference': move.name,
                'app_source': app_source  # custom code by aan
            })
        elif self.move_name:
            raise UserError(_('Operation not allowed. Since your statement line already received a number, '
                              'you cannot reconcile it entirely with existing journal entries '
                              'otherwise it would make a gap in the numbering. '
                              'You should book an entry '
                              'and make a regular revert of it in case you want to cancel it.'))
        counterpart_moves.assert_balanced()

        return counterpart_moves

    def _prepare_reconciliation_move_line(self, move, amount):
        result = super(AccountBankStatementLine, self)._prepare_reconciliation_move_line(move, amount)
        if self.statement_id.journal_id.is_voucher and self.pos_statement_id \
                and getattr(self, 'voucher_id'):
            result = self.process_payment_voucher(result, move, amount)
        return result

    def process_payment_voucher(self, result, move, amount):
        if self.voucher_id and not self.voucher_id.is_external:
            # process voucher internal
            # replace debit account with expense account on voucher
            result['account_id'] = self.voucher_id.expense_account_id.id

        else:
            # process voucher external
            # TODO: voucher external jika nilai voucher > total order, how to handle it?

            # accounting notes:
            # 1. POS Sales: Confirm pos order
            #       debit: AR Trade/Guest Ledger
            #           credit: Revenue (food/beverage/etc)
            #    step 0 -- Odoo as is process -- Done
            # 2. create move line
            #       debit: self.statement_id.journal_id.default_credit_account_id.id
            #           credit: AR Trade/Guest Ledger
            #    existing process in _prepare_reconciliation_move_line
            #       done - nothing changes
            # 3. create invoice to charge external company (owner of the voucher), with journal:
            #       debit: AR Trade (company)
            #           credit: self.statement_id.journal_id.default_credit_account_id.id

            # these codes is for no 3
            order = self.pos_statement_id
            partner = self.voucher_id.partner_id
            # partner = order.customer_id.property_account_receivable_id.id
            invoice_journal = self.statement_id.journal_id
            statement_payment_amount_used = self.amount
            account_id_invoice_line = invoice_journal.default_credit_account_id.id

            self.create_invoice_from_pos_payment(
                order, partner, invoice_journal, account_id_invoice_line,
                statement_payment_amount_used)

        return result

    def create_invoice_from_pos_payment(self, order, partner,
                                        invoice_journal, account_id_invoice_line,
                                        statement_payment_amount_used):
        # partner = order.customer_id.property_account_receivable_id.id
        receivable_account_id = partner.property_account_receivable_id.id if partner else None
        if not receivable_account_id:
            raise UserError(
                _('There is no receivable account defined for customer "%s"') %
                (partner.name,))

        invoice = self.env['account.invoice']
        values = {
            'date_invoice': order.session_id.working_date,  # TODO: make sure its valid
            'partner_id': partner.id,
            'currency_id': order.pricelist_id.currency_id.id,
            'account_id': receivable_account_id,
            'user_id': order.user_id.id,
            'journal_id': invoice_journal.id,
            'company_id': order.company_id.id,
            'origin': order.name,
            'invoice_line_ids': [],
            'app_source': 'pos'
        }
        line_values = {
            'name': order.name,
            # 'product_id': line.product_id.id,
            'account_id': account_id_invoice_line,
            # 'account_id': order.customer_id.expense_account_id.id,
            'quantity': 1,
            'price_unit': statement_payment_amount_used or 0,
            # 'invoice_line_tax_ids': [(6, 0, line.tax_ids.mapped('id'))] or False,
        }
        values['invoice_line_ids'].append((0, 0, line_values))
        curr_invoice = invoice.create(values)
        order.invoice_id = curr_invoice
        # validate invoice
        curr_invoice.action_invoice_open()
