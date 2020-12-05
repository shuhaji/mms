# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# from Odoo.local.kg_account.controllers.terbilang import terbilang
from odoo.addons.kg_account.controllers.terbilang import terbilang
from odoo import api, fields, models, _
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools import config
import datetime
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError


class KGInvoiceCollecting(models.Model):
    _name = 'invoice.collecting'

    name = fields.Char(
        'Name',
    )
    company_id = fields.Many2one(
        'res.company', string='Company', change_default=True,
        required=True, readonly=True,
        default=lambda self: self.env.user.company_id)

    notes = fields.Text(
        'Notes',
    )

    date = fields.Date(
        'Date',
        default=fields.Date.today
    )

    partner_id = fields.Many2one(
        'res.partner',
        'Customer',
    )

    invoice_collecting_line_ids = fields.One2many(
        'invoice.collecting.line',
        'invoice_collecting_id',
        'Invoice Collecting Lines',
    )

    invoice_line_ids = fields.Many2many(
        'account.invoice',
        'collecting_invoice_rel',
        'collecting_id',
        'invoice_id',
        string='Invoice List', required=True)

    total_invoice = fields.Float('Total Invoice', compute='compute_total_invoice', store=True)
    total_residual = fields.Float('Total Balance', compute='compute_total_invoice', store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        # ('collected', 'Collected'),
        ('partial_paid', 'Partial Paid'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], default='draft')

    terbilang = fields.Char(compute='compute_total_invoice')

    print_counter = fields.Float(
        'Print Counter',
        default=0,
        digits=dp.get_precision('counter'),
    )

    # Bank journals fields
    bank_account_id = fields.Many2one('res.partner.bank', string='Bank Account', ondelete='restrict', domain="[('company_id', '=', company_id)]")
    bank_acc_number = fields.Char(related='bank_account_id.acc_number')
    bank_acc_holder_name = fields.Char()
    bank_id = fields.Many2one('res.bank', related='bank_account_id.bank_id')

    @api.one
    def button_cancel(self):
        if self.invoice_line_ids:
            for inv in self.invoice_line_ids:
                if inv.residual < inv.amount_total:
                    raise UserError('Some invoice is already paid partial or fully paid. '
                                    'You not allowed to cancel this invoice collecting!')
                inv.write({
                    'collecting_status': '',
                    'invoice_collecting_id': False,
                })
        self.state = 'cancel'

    @api.depends('invoice_line_ids')
    def compute_total_invoice(self):
        for rec in self:
            rec.total_invoice = sum(invoice.amount_total for invoice in rec.invoice_line_ids)
            rec.total_residual = sum(invoice.residual for invoice in rec.invoice_line_ids)

        self.terbilang = terbilang(self.total_invoice, 'idr', 'id')

    @api.model
    def create(self, vals):
        self.env['account.period'].check_lock_period(
            self, vals.get('company_id'), vals.get('date'), trx_type="is_ar_closed")

        vals['name'] = self.env['ir.sequence'].next_by_code('invoice.collecting')
        result = super(KGInvoiceCollecting, self).create(vals)

        # if not vals.get('invoice_line_ids'):
        #     raise ValidationError(_('You cannot save invoice collecting with no lines!'))

        if vals.get('invoice_line_ids', False):
            invoice = self.env['account.invoice']
            for record in vals['invoice_line_ids']:
                invoice = invoice.browse(record[2])
                for i in invoice:
                    i.invoice_collecting_id = result.id
                    i.collecting_status = 'draft'
        return result

    @api.multi
    def write(self, vals):
        if vals.get('date'):
            for rec in self:
                # validate old date
                rec.env['account.period'].check_lock_period(
                    rec, rec.company_id, rec.date, trx_type="is_ar_closed")
                # validate new date
                rec.env['account.period'].check_lock_period(
                    rec, rec.company_id, vals.get('date'), trx_type="is_ar_closed")

        old_invoice = self.invoice_line_ids.ids

        if vals.get('invoice_line_ids', False):
            invoice = self.env['account.invoice']
            new_invoice = []

            for record in vals['invoice_line_ids']:
                new_invoice.append(record[2])
                invoice = invoice.browse(record[2])

                for inv in invoice:
                    inv.invoice_collecting_id = self.id

                    if self.state in ['draft']:
                        inv.collecting_status = self.state
        res = super(KGInvoiceCollecting, self).write(vals)

        for inv in old_invoice:
            if inv not in self.invoice_line_ids.ids:
                self.env['account.invoice'].browse(inv).write({
                    'collecting_status': False,
                    'invoice_collecting_id': False,
                })

        return res

    @api.multi
    def unlink(self):
        for inv in self.invoice_line_ids:
            inv.write({
                'collecting_status': False,
                'invoice_collecting_id': False,
            })

    # @api.multi
    # @api.constrains('partner_id', 'invoice_collecting_line_ids')
    # def check_line(self):
    #     for collect in self:
    #         if not collect.invoice_collecting_line_ids:
    #             raise ValidationError(_('You cannot save invoice collecting with no lines!'))

    # used to show wizard of invoice but still cant find the way to show search and filter menu bar
    # @api.multi
    # def show_invoices(self):
    #     for billing in self:
    #         view_id = self.env.ref('kg_account.kg_show_invoices')
    #         search_id = self.env.ref('kg_account.kg_show_invoices_search')
    #         import pdb; pdb.set_trace()
    #         return {
    #             'domain': "[]",
    #             'name': _('Invoices'),
    #             'view_type': 'form',
    #             'view_mode': 'form',
    #             'res_model': 'invoice.collecting.wizard',
    #             'view_id': view_id.id,
    #             'target': 'new',
    #             'type': 'ir.actions.act_window'
    #         }
    # end of code

    # @api.multi
    # @api.onchange('invoice_collecting_line_ids')
    # def onchange_invoice_collecting_line(self):
    #     used_invoices = []
    #     for collect in self:
    #         for line in collect.invoice_collecting_line_ids:
    #             if not collect.name:
    #                 if line.invoice_id.id in used_invoices:
    #                     raise ValidationError(_('This invoice is already selected!'))
    #                 used_invoices.append(line.invoice_id.id)

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.invoice_line_ids = False

        # search partners invoice with state open
        partner_list = []
        partner_ids = self.env['account.invoice'].search([
            ('state', '=', 'open'),
            ('type', '=', 'out_invoice'),
            ('collecting_status', 'in', ['', False, 'selected']),
            ('company_id', '=', self.env.user.company_id.id)
        ])
        for p in partner_ids:
            if p.partner_id.id not in partner_list:
                partner_list.append(p.partner_id.id)

        domain_partner_id = [('id', 'in', partner_list)]

        return {'domain': {
            'partner_id': domain_partner_id}}

    # @api.onchange('invoice_line_ids')
    # def onchange_invoice_line_ids(self):
    #     if self.invoice_line_ids:
    #         for inv in self.invoice_line_ids:
    #             inv.write({'collecting_status':'selected'})

    @api.multi
    def print_report(self):
        if self.print_counter > 0 and \
                not self.env.user.has_group('kg_account.group_invoice_collecting'
                                            '_duplicate_report_access_rights'):
            raise ValidationError(_("You don't have "
                                    "access to re-print Invoice Collecting Report !"))
        self.print_counter += 1
        data = {
            'ids': self.ids,
            'model': self,
            'model_name': self._name,
        }

        return self.env.ref('kg_account.invoice_collecting_report_action').report_action(self, data=data)

    @api.multi
    def print_receipt(self):
        data = {
            'ids': self.ids,
            'model': self,
            'model_name': self._name,
        }

        return self.env.ref('kg_account.invoice_collecting_receipt_action').report_action(self, data=data)


class KGInvoiceCollectingLine(models.Model):
    _name = 'invoice.collecting.line'

    invoice_collecting_id = fields.Many2one(
        'invoice.collecting',
        'Invoice Collecting',
    )

    invoice_id = fields.Many2one(
        'account.invoice',
        'Invoice',
    )

    name = fields.Char(
        'Invoice',
    )

    partner_id = fields.Many2one(
        'res.partner',
        'Customer',
    )

    partner_temp_id = fields.Many2one(
        'res.partner',
        'Customer',
        compute='set_value_line'
    )

    date_due = fields.Datetime(
        'Due Date',
    )

    date_due_temp = fields.Datetime(
        'Due Date',
        compute='set_value_line'
    )

    amount_total = fields.Float(
        'Total Invoice',
        default=0,
    )

    amount_total_temp = fields.Float(
        'Total Invoice',
        default=0,
        compute='set_value_line'
    )

    residual = fields.Float(
        'Balance',
        default=0,
    )

    residual_temp = fields.Float(
        'Balance',
        default=0,
        compute='set_value_line'
    )

    terbilang = fields.Char(compute='set_value_line')

    @api.multi
    @api.depends('invoice_id')
    def set_value_line(self):
        for line in self:
            if line.partner_id:
                line.partner_temp_id = line.partner_id

            if line.date_due:
                line.date_due_temp = line.date_due

            if line.amount_total:
                line.amount_total_temp = line.amount_total
                line.terbilang = terbilang(line.amount_total, 'idr', 'id')

            if line.residual:
                line.residual_temp = line.residual

    @api.multi
    @api.depends('invoice_collecting_id.partner_id')
    def set_value_line(self):
        for line in self:
            if line.partner_id:
                line.partner_temp_id = line.partner_id

            if line.date_due:
                line.date_due_temp = line.date_due

            if line.amount_total:
                line.amount_total_temp = line.amount_total
                line.terbilang = terbilang(line.amount_total, 'idr', 'id')

            if line.residual:
                line.residual_temp = line.residual

    @api.multi
    @api.onchange('invoice_id')
    def onchange_invoice_id(self):
        for line in self:
            line.partner_id = line.invoice_id.partner_id.id
            line.name = line.invoice_id.number
            line.date_due = line.invoice_id.date_due
            line.amount_total = line.invoice_id.amount_total
            line.residual = line.invoice_id.residual
            if not line.invoice_collecting_id.partner_id:
                raise ValidationError(_('You must select customer first!'))

            if line.partner_id:
                if line.invoice_collecting_id.partner_id != line.partner_id:
                    raise ValidationError(_('You cannot select invoice which has different customer '
                                            'with invoice collecting customer!'))


class KGInvoiceCollectingReport(models.AbstractModel):
    _name = 'report.kg_account.invoice_collecting_report'

    @api.multi
    def get_report_values(self, docids, data=None):
        if data:
            ids = data['ids']
            report_model = self.env[data['model_name']].browse(ids)
            docargs = {
                'doc_ids': report_model.ids,
                'doc_model': data['context']['active_model'],
                'docs': report_model,
            }
        if not data:
            if self._name == 'report.kg_account.invoice_collecting_report':
                ids = docids
                report_model = self.env['invoice.collecting'].browse(ids)
                for report in report_model:
                    if report.print_counter > 0 and \
                            not self.env.user.has_group('kg_account.group_invoice_collecting_duplicate_report_access_rights'):
                        raise ValidationError(_("You don't have "
                                                "access to re-print Invoice Collecting Report !"))
                    report.print_counter += 1

                docargs = {
                    'doc_ids': report_model.ids,
                    'doc_model': self.env['invoice.collecting']._name,
                    'docs': report_model,
                }
        return docargs
