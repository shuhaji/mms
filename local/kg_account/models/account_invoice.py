# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# from Odoo.local.kg_account.controllers.terbilang import terbilang
from odoo.addons.kg_account.controllers.terbilang import terbilang
from odoo import api, fields, models, _
from odoo import api, fields, models, tools, SUPERUSER_ID, _
import datetime
from lxml import etree
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError


class KGAccountInvoice(models.Model):
    _inherit = 'account.invoice'

    is_allow_edit_invoice = fields.Boolean(
        'Allow Edit Invoice',
        default=False,
        compute='allow_edit_invoice',
    )

    invoice_collecting_id = fields.Many2one(
        comodel_name='invoice.collecting',
        string='Invoice Collecting',
        copy=False
    )

    # invoice from pms or pos or others?
    app_source = fields.Char(default='')

    collecting_status = fields.Selection(
        [
            ('selected', 'Selected'),
            ('draft', 'Draft'),
            ('partial_paid', 'Partial Paid'),
            ('done', 'Done')
        ],
        copy=False,
    )

    terbilang = fields.Char(
        compute='_get_value_terbilang',
        store=False,
    )

    print_counter = fields.Float(
        'Print Counter',
        digits=dp.get_precision('Print Counter'),
        default=0.0,
    )

    show_print_invoice_unsent = fields.Boolean(
        'Show Print Invoice Unsent',
        default=False,
        compute='set_show_print_invoice',
    )

    show_print_invoice_sent = fields.Boolean(
        'Show Print Invoice Sent',
        default=False,
        compute='set_show_print_invoice',
    )

    print_via_button = fields.Boolean(
        'Print Invoice via Button Print Invoice',
        default=False,
    )

    report_counter = fields.Float(
        'Report Counter',
        compute='set_report_counter',
        default=0.0,
    )

    show_credit_note = fields.Boolean(
        'Show Credit Note',
        default=True,
        compute='set_show_credit_note',
    )

    show_button_cancel_invoice = fields.Boolean(
        'Show Button Cancel Invoice',
        default=False,
        compute='set_show_button_cancel_invoice',
    )

    amount_untaxed = fields.Monetary(
        compute='_compute_amount',
        string='Untaxed Amount'
    )
    amount_service = fields.Monetary(
        compute='_compute_amount',
        string='Service')
    amount_tax_only = fields.Monetary(
        compute='_compute_amount',
        string='Tax')
    amount_tax = fields.Monetary(
        compute='_compute_amount',
        string='Taxes + Services',
        track_visibility='none')
    # brutto_before_tax = fields.Monetary(
    #     compute='_compute_amount',
    #     string='Total Brutto w/o tax', store=False)
    # total_disc_amount_before_tax = fields.Monetary(
    #     compute='_compute_amount',
    #     string='Discount w/o Tax', store=False)

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'tax_line_ids.amount_rounding',
                 'currency_id', 'company_id', 'date_invoice', 'type')
    def _compute_amount(self):
        super(KGAccountInvoice, self)._compute_amount()
        round_curr = self.currency_id.round
        self.amount_service = round_curr(
            sum(line.service_amount for line in self.invoice_line_ids))
        self.amount_tax_only = round_curr(
            sum(line.tax_amount for line in self.invoice_line_ids))


    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(KGAccountInvoice, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        current_user = self.env['res.users'].browse(self.env.context.get('uid', False))
        doc = etree.fromstring(res['arch'])

        if self.env.context.get('default_type', False) == 'out_refund' \
            and self.env.context.get('type', False) == 'out_refund' \
                and self.env.context.get('journal_type') == 'sale':
                    if not current_user.has_group('kg_account.group_allow_add_credit_note'):
                        doc.set('create', 'false')
                        res['arch'] = etree.tostring(doc)

        return res

    @api.multi
    def allow_edit_invoice(self):
        for invoice in self:
            current_user = self.env['res.users'].browse(self.env.context.get('uid', False))
            if invoice.state in ['draft', 'open']:
                if current_user.has_group('kg_account.group_allow_to_edit_invoice'):
                    invoice.is_allow_edit_invoice = True
            else:
                invoice.is_allow_edit_invoice = False

    @api.multi
    @api.depends('activity_user_id')
    def set_show_button_cancel_invoice(self):
        for invoice in self:
            current_user = self.env['res.users'].browse(self.env.context.get('uid', False))
            if invoice.state in ['draft', 'open']:
                if current_user.has_group('kg_account.group_allow_cancel_invoice'):
                    invoice.show_button_cancel_invoice = True
            else:
                invoice.show_button_cancel_invoice = False

    @api.multi
    @api.depends('activity_user_id')
    def set_show_credit_note(self):
        for invoice in self:
            current_user = self.env['res.users'].browse(self.env.context.get('uid', False))
            if not current_user.has_group('kg_account.group_allow_add_credit_note'):
                invoice.show_credit_note = False
            else:
                invoice.show_credit_note = True

    @api.multi
    @api.depends('print_counter')
    def set_report_counter(self):
        for invoice in self:
            invoice.report_counter = invoice.print_counter - 1

    @api.one
    # @api.depends('amount_total')
    def _get_value_terbilang(self):
        if self.amount_total:
            self.terbilang = terbilang(self.amount_total, 'idr', 'id')
        else:
            self.terbilang = ""
        # self.terbilang = 'Satu Juta'

    @api.multi
    def print_receipt(self):
        account_invoice = self
        data = {
            'ids': account_invoice.ids,
            'model': account_invoice,
            'model_name': account_invoice._name,
        }

        return self.env.ref('kg_account.invoice_customer_receipt_action').report_action(self, data=data)

    @api.multi
    def set_show_print_invoice(self):
        for invoice in self:
            current_user = self.env['res.users'].browse(self.env.context.get('uid', False))
            if invoice.state in ['open', 'paid']:
                if invoice.sent:
                    if current_user.has_group('kg_account.group_invoice_duplicate_report_access_rights'):
                        invoice.show_print_invoice_sent = True
                    elif not current_user.has_group('kg_account.group_invoice_duplicate_report_access_rights'):
                        if not invoice.print_counter > 0:
                            invoice.show_print_invoice_sent = True
                elif not invoice.sent:
                    if current_user.has_group('kg_account.group_invoice_duplicate_report_access_rights'):
                        invoice.show_print_invoice_unsent = True
                    elif not current_user.has_group('kg_account.group_invoice_duplicate_report_access_rights'):
                        if not invoice.print_counter > 0:
                            invoice.show_print_invoice_unsent = True
            elif invoice.state == 'draft':
                invoice.show_print_invoice_unsent = True

    @api.multi
    def increase_print_counter(self):
        for rec in self:
            if rec.state in ['open', 'paid']:
                rec.print_counter += 1

    @api.multi
    def invoice_print(self):
        # used when we want to reset print counter to 0
        # self.print_counter = 0
        # end of code
        self.increase_print_counter()
        self.print_via_button = True
        res = super(KGAccountInvoice, self).invoice_print()
        return res

    @api.model
    def cancel_applied_payment(self, payment_id, invoice_id):
        # unrenconcile a payment in an invoice
        self.move_id.line_ids.with_context(
            invoice_id=invoice_id,
            payment_id=payment_id).remove_move_reconcile()
        # self.env['account.move.line'].with_context(
        #     invoice_id=invoice_id,
        #     payment_id=payment_id
        # ).remove_move_reconcile()

    # @api.model
    # def name_search(self, name, args=None, operator='ilike', limit=100):
    #     res = super(KGAccountInvoice, self).name_search(name, args=None, operator=operator, limit=limit)
    #     args = args or []
    #     domain = []
    #     used_invoices = self.env['invoice.collecting'].search([
    #             ('invoice_line_ids', '!=', False)
    #             # ('invoice_collecting_line_ids', '!=', False)
    #         # ]).mapped('invoice_collecting_line_ids').mapped('invoice_id').mapped('id')
    #         ]).mapped('invoice_line_ids').mapped('invoice_id').mapped('id')
    #     domain = [('id', 'not in', used_invoices), ('state', '=', 'open'), ('type','=','out_invoice')]
    #     invoice = self.search(domain + args)

    #     return invoice.name_get()


class KGAccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    pms_check_in_date = fields.Datetime()
    pms_check_out_date = fields.Datetime()
    pms_folio_id = fields.Char()

    price_subtotal = fields.Monetary(
        string='Subtotal w/o Tax',
        store=True, readonly=True, compute='_compute_price',
        help="Total amount without taxes")
    price_total = fields.Monetary(
        string='Subtotal',
        store=True, readonly=True, compute='_compute_price',
        help="Total amount with taxes")
    service_amount = fields.Float(compute='_compute_price', digits=0, string='Service Amount', store=True)
    tax_amount = fields.Float(compute='_compute_price', digits=0, string='Tax Amount', store=True)

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
                 'invoice_id.date_invoice', 'invoice_id.date')
    def _compute_price(self):
        super(KGAccountInvoiceLine, self)._compute_price()
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(
                price, currency, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
        service_amount = taxes['total_service_amount'] if taxes else 0
        # self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price
        # self.price_total = taxes['total_included'] if taxes else self.price_subtotal
        tax_amount = self.price_total - self.price_subtotal - service_amount
        self.service_amount = service_amount
        self.tax_amount = tax_amount




