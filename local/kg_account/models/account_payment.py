# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime

from lxml import etree

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError, ValidationError


class KGAccountPayment(models.Model):
    _inherit = 'account.payment'
    _order = 'id desc'

    deposit_type_id = fields.Many2one(
        'deposit.type',
        'Deposit Type',
    )

    validate_date = fields.Date(
        'Validate Date',
        default=fields.Date.today,
        readonly=True
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('posted', 'Posted'),
        ('sent', 'Sent'),
        ('reconciled', 'Reconciled'),
        ('cancelled', 'Cancelled')],
    )

    allow_validate = fields.Boolean(
        'Allow validate',
        default=False,
        compute='set_allow_validate'
    )

    residual_temp = fields.Monetary(
        string='Remaining Amount', 
        related='residual',
        store=True,
        help="Remaining amount to apply."
    )

    # from pms or others?
    app_source = fields.Char(default='')

    # admin/bank fee details
    payment_line_ids = fields.One2many(
        'account.payment.line',
        'payment_id',
        'Admin/Bank Fee',
    )

    # Credit Card/EDC Settlement/Funded
    # acquirer transaction that will be settled/funded on this payment transfer
    acquirer_ids = fields.One2many(
        'kg.acquirer.transaction',
        'payment_id',
        'Trx CC yg Dicairkan/Funded')
    # temporary fields to allow multi selection for acquirer_ids
    acquirer_id_selection = fields.Many2many(
        'kg.acquirer.transaction',
        'account_payment_kg_acquirer_transaction_rel',
        'payment_id',
        'apply_id',
        'Select CC/Cash Acquirer Payment',
        store=False,
        domain="[('type', '=', 1),('amount_remain', '>', 0),('journal_id', '=', journal_id)]"
    )

    total_transaction = fields.Float('Total Transaction', compute='compute_total_statement', store=True)
    total_admin = fields.Float('Total Adjustment', compute='compute_total_statement', store=True)

    total_amount_selected = fields.Float('Net Amount Selected', compute='compute_total_statement',
                                         store=False)

    is_bank_edc_credit_card = fields.Boolean(related='journal_id.is_bank_edc_credit_card',
                                             string='Fields used for attrs', readonly=True)

    writeoff_amount = fields.Monetary(string='Write-Off Amount', compute='_compute_write_off',
                                      readonly=True, store=True,
                                      help="Write-Off Amount (Payment Amount - Amount Invoice Paid")
    writeoff_label = fields.Char(
        string='Journal Item Label',
        help='Change label of the counterpart that will hold the payment difference',
        default='Adjustment')
    # Money flows from the journal_id's default_debit_account_id or default_credit_account_id to the destination_account_id
    # inherited, change attribute to store=True
    destination_account_id = fields.Many2one('account.account', compute='_compute_destination_account_id', readonly=True, store=True)

    @api.multi
    @api.depends('writeoff_account_id', 'move_line_ids')
    def _compute_write_off(self):
        for payment in self:
            writeoff_amount = 0
            if payment.writeoff_account_id:
                writeoff_line = payment.move_line_ids.filtered(lambda l: l.account_id == payment.writeoff_account_id)
                # write amount ==> payment amount + writeoff_amount = amount invoice paid
                # ex: payment amount 200 + write off amount (-20) == invoice paid (180)
                # in move lines:
                #  payment to bank (debit) = 200
                #       write off (credit)      =  20   --> -20
                #       AR Trade (credit)       = 180
                writeoff_amount = writeoff_line.debit - writeoff_line.credit if writeoff_line else 0
            payment.writeoff_amount = writeoff_amount

    @api.depends('acquirer_ids', 'payment_line_ids')
    def compute_total_statement(self):
        for rec in self:
            if rec.payment_type == 'transfer' and rec.is_bank_edc_credit_card:
                rec.total_transaction = sum(transaction.amount_transfer for transaction in rec.acquirer_ids)
                rec.total_admin = sum(admin.amount for admin in rec.payment_line_ids)

                rec.total_amount_selected = rec.env.user.company_id.currency_id.round(
                    rec.total_transaction - rec.total_admin)
                rec.amount = rec.total_amount_selected

    @api.multi
    @api.onchange('is_advance_payment')
    def set_allow_validate(self):
        for payment in self:
            if payment.is_advance_payment and payment.state == 'draft':
                self.allow_validate = True
            
            if not payment.is_advance_payment and payment.state == 'approved':
                self.allow_validate = True
            
    @api.multi
    def approved(self):
        for payment in self:
            self.validate_date = fields.Date.today()
            self.state = 'approved'

    @api.multi
    def post(self):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconciliable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconciliable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        for rec in self:
            # custom code by andi
            current_user = self.env['res.users'].browse(self.env.context.get('uid'))
            if not current_user.has_group('kg_account.group_payments_approve_access_rights'):
                if rec.state != 'draft':
                    raise UserError(_("Only a draft payment can be posted."))
            
            if not current_user.has_group('kg_account.group_payments_validate_access_rights'):
                if rec.state != 'approved':
                    raise UserError(_("Only a draft payment can be posted."))
            # end of custom code

            # orginal code
            # if rec.state != 'draft':
            #     raise UserError(_("Only a draft payment can be posted."))
            # end of original code

            if any(inv.state != 'open' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # Use the right sequence to set the name
            if rec.payment_type == 'transfer':
                sequence_code = 'account.payment.transfer'
            else:
                if rec.partner_type == 'customer':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.customer.invoice'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.customer.refund'
                if rec.partner_type == 'supplier':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.supplier.refund'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.supplier.invoice'
            rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(sequence_code)
            if not rec.name and rec.payment_type != 'transfer':
                raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

            amount_admin = 0
            amount_transaction = 0

            # Create the journal entry

            if rec.payment_type == 'transfer' and rec.is_bank_edc_credit_card:
                if rec.total_transaction:
                    amount_transaction = rec.total_transaction
                if rec.total_admin:
                    amount_admin = rec.total_admin
                amount = amount_transaction
            else:
                # original code
                amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)

            move = rec._create_payment_entry(amount)

            # In case of a transfer, the first journal entry created debited the source liquidity account and credited
            # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
            if rec.payment_type == 'transfer':
                # custom code:
                move.related_journal_id = rec.destination_journal_id

                transfer_credit_aml = move.line_ids.filtered(
                    lambda r: r.account_id == rec.company_id.transfer_account_id)

                if rec.payment_type == 'transfer' and rec.is_bank_edc_credit_card:
                    transfer_debit_aml = rec._create_transfer_acquirer_entry(amount_transaction, amount_admin)
                else:
                    transfer_debit_aml = rec._create_transfer_entry(amount)
                    transfer_debit_aml.move_id.related_journal_id = self.journal_id

                (transfer_credit_aml + transfer_debit_aml).reconcile()

            rec.write({'state': 'posted', 'move_name': move.name})
        return True

    def _create_transfer_acquirer_entry(self, amount_transaction, amount_admin):
        """ Create the journal entry corresponding to the 'incoming money' part of an internal transfer, return the reconciliable move line
        """
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        # amount = amount_transfer + amount_admin
        # debit, credit, amount_currency, dummy = aml_obj.with_context(date=self.payment_date).compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)
        # amount_currency = self.destination_journal_id.currency_id and self.currency_id.with_context(date=self.payment_date).compute(amount, self.destination_journal_id.currency_id) or 0

        dst_move = self.env['account.move'].create(self._get_move_vals(self.destination_journal_id))
        dst_move.related_journal_id = self.journal_id

        # menambah di journal/bank tujuan
        amount_received = amount_transaction - amount_admin
        debit, credit, amount_currency, dummy = aml_obj.with_context(date=self.payment_date).compute_amount_fields(
            amount_received, self.currency_id, self.company_id.currency_id)
        amount_currency = self.destination_journal_id.currency_id and self.currency_id.with_context(
            date=self.payment_date).compute(amount_received, self.destination_journal_id.currency_id) or 0
        dst_liquidity_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, dst_move.id)
        dst_liquidity_aml_dict.update({
            'name': _('Transfer from %s') % self.journal_id.name,
            'account_id': self.destination_journal_id.default_credit_account_id.id,
            'currency_id': self.destination_journal_id.currency_id.id,
            'journal_id': self.destination_journal_id.id})
        aml_obj.create(dst_liquidity_aml_dict)

        # menambah biaya admin
        if amount_admin != 0:
            for adm_fee in self.payment_line_ids:
                debit, credit, amount_currency, dummy = aml_obj.with_context(date=self.payment_date).compute_amount_fields(
                    adm_fee.amount, self.currency_id, self.company_id.currency_id)
                amount_currency = self.destination_journal_id.currency_id and self.currency_id.with_context(
                    date=self.payment_date).compute(adm_fee.amount, self.destination_journal_id.currency_id) or 0

                dst_liquidity_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, dst_move.id)

                dst_liquidity_aml_dict.update({
                    # 'name': _('Biaya admin from %s') % self.journal_id.name,
                    'name': adm_fee.description,
                    'account_id': adm_fee.account_id.id,
                    'currency_id': self.destination_journal_id.currency_id.id,
                    'journal_id': self.destination_journal_id.id})
                aml_obj.create(dst_liquidity_aml_dict)

        amount_liquidity = amount_transaction

        debit, credit, amount_currency, dummy = aml_obj.with_context(date=self.payment_date).compute_amount_fields(
            amount_liquidity, self.currency_id, self.company_id.currency_id)
        amount_currency = self.destination_journal_id.currency_id and self.currency_id.with_context(
            date=self.payment_date).compute(amount_liquidity, self.destination_journal_id.currency_id) or 0

        transfer_debit_aml_dict = self._get_shared_move_line_vals(credit, debit, 0, dst_move.id)
        transfer_debit_aml_dict.update({
            'name': self.name,
            'account_id': self.company_id.transfer_account_id.id,
            'journal_id': self.destination_journal_id.id})
        if self.currency_id != self.company_id.currency_id:
            transfer_debit_aml_dict.update({
                'currency_id': self.currency_id.id,
                'amount_currency': -amount_currency  # -self.amount,
            })
        transfer_debit_aml = aml_obj.create(transfer_debit_aml_dict)
        dst_move.post()
        return transfer_debit_aml

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(KGAccountPayment, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                            submenu=submenu)
        if view_type != 'search' and self.env.uid != SUPERUSER_ID\
                and (res['name'] == 'account.payment.tree' or res['name'] == 'account.payment.form'):
            # Only for Sales/Customer Payment --> res['name'] == 'account.payment.tree'
            # Check if user is in group that allow creation
            has_hide_create_button_group = self.env.user.has_group('kg_account.group_hide_btn_create_payment')
            if has_hide_create_button_group:
                root = etree.fromstring(res['arch'])
                root.set('create', 'false')
                res['arch'] = etree.tostring(root)

        return res

    @api.multi
    @api.constrains('amount', 'total_amount_selected')
    def validate_amount(self):
        for rec in self:
            if rec.payment_type == 'transfer' and rec.is_bank_edc_credit_card:
                amount = self.env.user.company_id.currency_id.round(rec.amount)
                total_selected = self.env.user.company_id.currency_id.round(rec.total_amount_selected)
                if amount != total_selected:
                    raise ValidationError(_("Amount did not match!"))

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.payment_type == 'transfer' and rec.is_bank_edc_credit_card:
                for acq in rec.acquirer_ids:
                    acq.unlink()
                # self.env['kg.acquirer.transaction'].unlink(0, -rec.amount, rec.id)
        super(KGAccountPayment, self).unlink()

    # UPDATE INVOICE COLLECTING STATUS TO DONE WHEN ALL RELATED INVOICES IS FULLY PAID
    @api.multi
    def action_validate_invoice_payment(self):
        res = super(KGAccountPayment, self).action_validate_invoice_payment()
        if self.invoice_ids:
            for inv in self.invoice_ids:

                if inv.invoice_collecting_id:
                    total_invoice = sum(l.amount_total for l in inv.invoice_collecting_id.invoice_line_ids)
                    total_residual = sum(l.residual for l in inv.invoice_collecting_id.invoice_line_ids)

                    if total_invoice != total_residual:
                        if total_residual == 0:
                            inv.invoice_collecting_id.write({'state': 'done'})

                            # invoice update
                            for i in inv.invoice_collecting_id.invoice_line_ids:
                                i.write({'collecting_status': 'done'})
                        if total_residual > 0:
                            inv.invoice_collecting_id.write({'state': 'partial_paid'})

                            # invoice update
                            for i in inv.invoice_collecting_id.invoice_line_ids:
                                i.write({'collecting_status': 'partial_paid'})
        return res

    @api.onchange('acquirer_id_selection')
    def onchange_acquirer_id_selection(self):
        new_settlements = []
        existing_acquirer_ids = [acquirer.apply_id.id for acquirer in self.acquirer_ids]
        for data in self.acquirer_id_selection:
            if data.id not in existing_acquirer_ids:
                new_settlements.append([0, 0, {
                    'apply_id': data.id,
                    'date': self.payment_date,
                    'amount_transfer': data.amount_remain
                }])
        self.acquirer_ids = new_settlements

        self.acquirer_id_selection = False

        domain = self.set_domain_for_acquirer_ids()
        return domain

    @api.onchange('journal_id')
    def onchange_journal_id(self):
        if self.payment_type == 'transfer' and self.acquirer_ids:
            if self.journal_id.id != self.acquirer_ids[0].journal_id.id:
                warning = {
                    'title': 'Warning',
                    'message': 'Journal must be same with Existing Acquirer Settlement!'
                }
                return {'value': {'journal_id': self._origin.journal_id.id if self._origin.journal_id else False},
                        'warning': warning}
        domain = self.set_domain_for_acquirer_ids()
        return domain

    @api.onchange('acquirer_ids')
    def onchange_acquirer_ids(self):
        domain = self.set_domain_for_acquirer_ids()
        return domain

    def set_domain_for_acquirer_ids(self):
        domain_apply_id = [('type', '=', 1),
                           ('amount_remain', '>', 0)]
        if self.payment_type == 'transfer':
            # filtered out already selected transaction (prevent double select for current payment)
            # get already selected cc/acquirer transaction on this payment (to be excluded)
            if self.journal_id:
                domain_apply_id.append(('journal_id', '=', self.journal_id.id))
            if self.acquirer_ids:
                selected_ids = [acq.apply_id.id for acq in self.acquirer_ids if acq.apply_id]
                domain_apply_id.append(('id', 'not in', selected_ids))
        return {'domain': {
            'acquirer_id_selection': domain_apply_id
        }}

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(KGAccountPayment, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                            submenu=submenu)
        current_user = self.env['res.users'].browse(self.env.context.get('uid', False))
        doc = etree.fromstring(res['arch'])

        if self.env.context.get('default_type', False) == 'out_refund' \
                and self.env.context.get('type', False) == 'out_refund' \
                and self.env.context.get('journal_type') == 'sale':
            if not current_user.has_group('kg_account.group_allow_add_credit_note'):
                doc.set('create', 'false')
                res['arch'] = etree.tostring(doc)

        # if view_type == 'form':
        #     doc = etree.fromstring(res['arch'])
        #     nodes_acquirer_selection = doc.xpath("//field[@name='acquirer_id_selection']")
        #     if nodes_acquirer_selection:
        #         # if context.get('write_check', False):
        #         for node in nodes_acquirer_selection:
        #             domain = "[('type', '=', 1),('amount_remain', '>', 0),('journal_id', '=', journal_id)"
        #             if self.acquirer_ids:
        #                 domain = domain + ",('id', 'not in', {ids})".format(ids=self.acquirer_ids.ids)
        #             domain = domain + "]"
        #             node.set('domain', domain)
        #             # node.set('widget', '')
        #         res['arch'] = etree.tostring(doc)

        return res

    @api.onchange('payment_date')
    def onchange_payment_date(self):
        if self.payment_date:
            if not datetime.strptime(self.payment_date, DEFAULT_SERVER_DATE_FORMAT).date() <= datetime.now().date():
                warning = {
                    'title': 'Warning',
                    'message': 'Please select a payment date equal/or less than the current date'
                }
                return {'value': {'payment_date': False}, 'warning': warning}

            if self.payment_type == 'transfer':
                for a in self.acquirer_ids:
                    a.date = self.payment_date

                for p in self.payment_line_ids:
                    p.admin_date = self.payment_date
            return {'value': {'payment_date': self.payment_date}}

    @api.multi
    def cancel(self):
        result = super(KGAccountPayment, self).cancel()
        """
        fix for this bug/error:
        File "/usr/lib/python3.6/xmlrpc/client.py", line 528, in dump_nil
        raise TypeError("cannot marshal None unless allow_none is enabled")
        TypeError: cannot marshal None unless allow_none is enabled
        """
        # every method should return some value
        # OpenERP's XMLRPC protocol doesn't allow the None values to pass to the client
        return result if result is not None else True

    # @api.one
    # @api.depends('invoice_ids', 'payment_type', 'partner_type', 'partner_id')
    # def _compute_destination_account_id(self):
    #     # custom code:
    #     if not self.invoice_ids and not self.payment_type == 'transfer' and not self.partner_id:
    #         # original code, bug error if no rows exists in ir property for this res company and this field
    #         # self.destination_account_id = default_account.id
    #         # bug fix:
    #         if self.partner_type == 'customer':
    #             field_name = 'property_account_receivable_id'
    #         else:
    #             field_name = 'property_account_payable_id'
    #         default_account = self.env['ir.property'].get(field_name, 'res.partner')
    #         if not default_account:
    #             raise UserError(
    #                 _('Default {type} account not defined for this user company (ir.property - field: {field}).'.format(
    #                     type='Receivable' if self.partner_type == 'customer' else 'Payable',
    #                     field=field_name)))
    #     # end custom
    #     super(KGAccountPayment, self)._compute_destination_account_id()


class KGAccountPaymentLine(models.Model):
    _name = 'account.payment.line'
    # admin/bank fee details
    payment_id = fields.Many2one(
        'account.payment',
        'Account Payment',
        ondelete='cascade'
    )

    @api.model
    def default_get_account_id(self):
        # payment_id = self.env.context.get('payment_id')
        # payment_model = self.env.context.get('account.payment')
        # if payment_id and payment_model:
        #     payment_obj = self.env[payment_model].browse(payment_id)
        #     account_id = payment_obj.destination_journal_id.company_id.admin_fee_account_id
        #     return account_id
        # else:
        #     return False
        return self.env.user.company_id.admin_fee_account_id

    account_id = fields.Many2one(
        'account.account',
        'Account',
        required=True,
        default=default_get_account_id,
    )

    # admin_date = fields.Date(required=True, default=fields.Date.context_today)
    admin_date = fields.Date(string="Adjustment Date",
                             default=lambda self: self.payment_id.payment_date)
    description = fields.Char()
    amount = fields.Float()

    @api.onchange('account_id')
    def onchange_account_id(self):
        for rec in self:
            rec.admin_date = rec.payment_id.payment_date


class KGAccountRegisterPayments(models.TransientModel):
    _inherit = "account.register.payments"

    @api.onchange('payment_date')
    def onchange_payment_date(self):
        if self.payment_date:
            if not datetime.strptime(self.payment_date, DEFAULT_SERVER_DATE_FORMAT).date() <= datetime.now().date():
                warning = {
                    'title': 'Warning',
                    'message': 'Please select a payment date equal/or less than the current date'
                }
                return {'value': {'payment_date': False}, 'warning': warning}

            return {'value': {'payment_date': self.payment_date}}
