# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from addons.point_of_sale.models.pos_session import PosSession
from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
import datetime
import time


class KGPOSSession(models.Model):
    _inherit = 'pos.session'

    # Working_date odoo == working_date PMS
    #   start_at disimpan di database dalam bentuk DateTime UTC (GMT+00) di field postgres DateTime Without Timezone
    #   jika session kasir Room Service open/start at tgl 10 feb jam 1 malam WIB,
    #   maka akan tersimpan di database 2019-02-09T18:00:00  == GMT+00
    #   ini akan problem saat extract data ke analytics/BI,
    #  krn itu field ini dibutuhkan, akan terisi = Date Start at = 2019-02-10
    #  PENTING: pastikan setting timezone di master user sudah di set ke Asia/Jakarta
    #           atau Asia/Makasar atau Asia/Jayapura
    working_date = fields.Date(
        string='Working Date',
        required=True, states={'closed': [('readonly', True)]},
        index=True, copy=False, default=fields.Date.context_today,
        help="Active Working Date")

    # name_shift = fields.Char('Session')
    shift_id = fields.Many2one('hr.shift', string='Shift')
    name = fields.Char(string='Session ID', required=True, default='/')

    # @api.onchange('shift_id')
    # def _onchange_shift(self):
    #     orig_name = self._origin.name.replace('/' + self._origin.shift_id.code, "")
    #
    #     self.name = orig_name + '/' + self.shift_id.code
    #
    #     return self

    # code when we want to show pop up to select journal for applying advance payment
    # @api.multi
    # def action_pos_session_closing_control(self):
    #     self._check_pos_session_balance()
    #     for session in self:
    #         session.write({'state': 'closing_control', 'stop_at': fields.Datetime.now()})
    #         if not session.config_id.cash_control:
    #             if any(order.pos_advance_payment_ids for order in session.order_ids):
    #                 view_id = self.env.ref('kg_pos.wizard_adv_payment_journal_view')
    #                 return {
    #                         'domain': "[]",
    #                         'name': _('Select journal for applying advance payment'),
    #                         'view_type': 'form',
    #                         'view_mode': 'form',
    #                         'res_model': 'wizard.select.journal',
    #                         'view_id': view_id.id,
    #                         'target': 'new',
    #                         'type': 'ir.actions.act_window'
    #                         }
    #             else:
    #                 session.action_pos_session_close()
    # end of code

    # code when we want to show pop up to select journal for applying advance payment
    # @api.multi
    # def action_pos_session_validate(self):
    #     self._check_pos_session_balance()

    #     # custom code
    #     for session in self:
    #         if any(order.pos_advance_payment_ids for order in session.order_ids):
    #             view_id = self.env.ref('kg_pos.wizard_adv_payment_journal_view')

    #             return {
    #                     'domain': "[]",
    #                     'name': _('Select journal for applying advance payment'),
    #                     'view_type': 'form',
    #                     'view_mode': 'form',
    #                     'res_model': 'wizard.select.journal',
    #                     'view_id': view_id.id,
    #                     'target': 'new',
    #                     'type': 'ir.actions.act_window'
    #                     }
    #         else:
    #             session.action_pos_session_close()
    #     end of custom code

    #     original code
    #     self._check_pos_session_balance()
    #     self.action_pos_session_close()
    #     end of original code

    # end of code

    @api.model
    def create(self, values):
        res = super(KGPOSSession, self).create(values)
        for statement in res.statement_ids:
            statement.date = res.working_date
        return res

    @api.multi
    def write(self, values):
        res = super(KGPOSSession, self).write(values)
        if values.get('working_date'):
            for rec in self:
                for statement in rec.statement_ids:
                    if statement.date != values.get('working_date'):
                        statement.date = values.get('working_date')
        return res

    def _confirm_orders(self):
        for session in self:
            company = session.config_id.journal_id.company_id
            company_id = company.id
            orders = session.order_ids.filtered(lambda order: order.state == 'paid').sorted(key=lambda order: order.id)

            # custom code by andi
            for order in orders:

                if order.pos_advance_payment_ids:
                    if order.apply_id:
                        # refund process
                        order.post_refund_order_advance_payment()
                    else:
                        self.post_order_with_advance_payment(order)

                elif order.customer_id:
                    if order.apply_id:
                        # refund process
                        order.post_refund_order_city_ledger()
                    else:
                        self.post_order_cust_city_ledger(order, session)

            # end of custom code

            super(KGPOSSession, self)._confirm_orders()

            # journal_id = self.env['ir.config_parameter'].sudo().get_param(
            #     'pos.closing.journal_id_%s' % company_id, default=session.config_id.journal_id.id)
            # if not journal_id:
            #     raise UserError(_("You have to set a Sale Journal for the POS:%s") % (session.config_id.name,))
            #
            # move = self.env['pos.order'].with_context(force_company=company_id)._create_account_move(
            #     session.start_at, session.name, int(journal_id), company_id)
            # orders.with_context(force_company=company_id)._create_account_move_line(session, move)
            # for order in session.order_ids.filtered(lambda o: o.state not in ['done', 'invoiced']):
            #     if order.state not in ('paid'):
            #         raise UserError(
            #             _("You cannot confirm all orders of this session, because they have not the 'paid' status.\n"
            #               "{reference} is in state {state}, total amount: {total}, paid: {paid}").format(
            #                 reference=order.pos_reference or order.name,
            #                 state=order.state,
            #                 total=order.amount_total,
            #                 paid=order.amount_paid,
            #             ))
            #     order.action_pos_order_done()
            # orders_to_reconcile = session.order_ids._filtered_for_reconciliation()
            # orders_to_reconcile.sudo()._reconcile_payments()

    def post_order_cust_city_ledger(self, order, session):
        # TODO: refactor code, extract method to create invoice, use statement_line.create_invoice_from_pos_payment
        # new code: (belum sempat test, buka code ini, tutup yg old code, kemudian lakukan test)
        # statement_payment = None
        # statement_payment_amount_used = 0
        # partner = order.customer_id
        # if not partner:
        #     return False
        #
        # for st_line in order.statement_ids:
        #     if st_line.journal_id.is_city_ledger:
        #         statement_payment = st_line
        #         statement_payment_amount_used += st_line.amount
        #         invoice_journal = st_line.journal_id
        #         account_id_invoice_line = invoice_journal.default_credit_account_id.id
        # if statement_payment and statement_payment_amount_used > 0:
        #     statement_payment.create_invoice_from_pos_payment(
        #         order, partner, invoice_journal, account_id_invoice_line,
        #         statement_payment_amount_used)

        # old custom code:
        invoice = self.env['account.invoice']
        if order.customer_id.property_account_receivable_id.id:
            account_id = order.customer_id.property_account_receivable_id.id
        else:
            raise UserError(
                _('There is no receivable account defined for city ledger customer "%s"') %
                (order.customer_id.name,))
        if any(st_line.journal_id.is_city_ledger for st_line in order.statement_ids):
            city_ledger_journal = order.statement_ids.filtered(lambda st: st.journal_id.is_city_ledger)[
                0].journal_id
            related_journal = city_ledger_journal
            journal_id = city_ledger_journal.id
        else:
            related_journal = order.sale_journal
            journal_id = order.sale_journal.id
        # TODO: for RETURN transaction, create credit note and auto reconcile with the original invoice
        values = {
            'date_invoice': session.working_date,
            'partner_id': order.customer_id.id,
            'currency_id': order.pricelist_id.currency_id.id,
            'account_id': account_id,
            'user_id': order.user_id.id,
            'journal_id': journal_id,
            'company_id': order.company_id.id,
            'origin': order.name,
            'invoice_line_ids': [],
            'app_source': 'pos'
        }
        city_ledger_statement = order.statement_ids.filtered(lambda st: st.journal_id.is_city_ledger)
        city_ledger_amount_used = sum(cl_statement.amount for cl_statement in city_ledger_statement)
        vals = {
            'name': order.name,
            # 'product_id': line.product_id.id,
            'account_id': related_journal.default_credit_account_id.id,
            # 'account_id': order.customer_id.expense_account_id.id,
            'quantity': 1,
            'price_unit': city_ledger_amount_used or 0,
            # 'invoice_line_tax_ids': [(6, 0, line.tax_ids.mapped('id'))] or False,
        }
        values['invoice_line_ids'].append((0, 0, vals))
        curr_invoice = invoice.create(values)
        order.invoice_id = curr_invoice
        # validate invoice
        curr_invoice.action_invoice_open()

    def post_order_with_advance_payment(self, order):
        invoice = self.env['account.invoice']
        if order.partner_id.property_account_receivable_id.id:
            account_id = order.partner_id.property_account_receivable_id.id
        else:
            raise UserError(
                _('There is no receivable account defined for customer "%s"') %
                (order.partner_id.name,))
        if any(journal.is_advance_payment for journal in order.statement_ids.mapped('journal_id')):

            journal = order.statement_ids.filtered(lambda st: (
                    st.journal_id.is_advance_payment == True
            )).mapped('journal_id')[-1]

            journal_id = journal.id

        else:
            journal_id = order.sale_journal.id
        values = {
            'partner_id': order.partner_id.id,
            'currency_id': order.pricelist_id.currency_id.id,
            'account_id': account_id,
            'user_id': order.user_id.id,
            'journal_id': journal_id,
            'company_id': order.company_id.id,
            'origin': order.name,
            'invoice_line_ids': [],
            'app_source': 'pos'
        }
        for payment in order.pos_advance_payment_ids:
            vals = {
                'name': payment.name,
                'account_id': payment.advance_payment_account_id.id,
                'quantity': 1,
                'price_unit': payment.adv_payment_amount_used,
            }
            values['invoice_line_ids'].append((0, 0, vals))
        curr_invoice = invoice.create(values)
        order.invoice_id = curr_invoice
        # validate invoice
        curr_invoice.action_invoice_open()
        account_adv_payment_inv = self.env['account.advance.payment.invoice']
        real_adv_payment_id = order.pos_advance_payment_ids.mapped('adv_payment_id')
        real_adv_payment = self.env['account.payment'].browse(real_adv_payment_id)
        # code to apply journal from pop up wizard when validatin POS session
        # if self.env.context.get('adv_payment_journal', False):
        #     journal = self.env.context.get('adv_payment_journal', False)
        # else:
        #     journal = curr_invoice.journal_id
        # end of code
        journal = curr_invoice.journal_id
        order.invoice_id = curr_invoice
        value = {
            'journal_id': journal.id,
            'date': fields.date.today(),
            'advance_payment_ids': [(6, 0, real_adv_payment.ids)]
        }
        account_adv_payment_inv = account_adv_payment_inv.with_context(
            active_model=curr_invoice._name,
            active_ids=curr_invoice.mapped('id'),
            active_id=curr_invoice.id).create(
            value)
        account_adv_payment_inv.apply_advance_payment()
        # code for sending data to PMS
        post_request = self.env['pos.helpers']
        post_request.post_adv_payment(advance_payments=account_adv_payment_inv.advance_payment_ids)
        # end of code

    @api.multi
    def action_pos_session_close(self):
        # Close CashBox
        for session in self:
            # custom code, get date from working date field
            # start_date = datetime.datetime.strptime(session.start_at, "%Y-%m-%d %H:%M:%S").date()
            start_date = fields.Date.from_string(session.working_date)
            # end of custom code

            company_id = session.config_id.company_id.id
            ctx = dict(self.env.context, force_company=company_id, company_id=company_id)
            for st in session.statement_ids:
                # custom code
                st.date = session.working_date
                order_with_same_journal_id = session.order_ids.filtered(
                    lambda order:
                    (
                            st.journal_id.id in order.statement_ids.mapped('journal_id').mapped('id')
                    )
                )
                # end of custom code

                if abs(st.difference) > st.journal_id.amount_authorized_diff:
                    # The pos manager can close statements with maximums.
                    if not self.user_has_groups("point_of_sale.group_pos_manager"):
                        raise UserError(_(
                            "Your ending balance is too different from the theoretical cash closing (%.2f), "
                            "the maximum allowed is: %.2f. You can contact your manager to force it.") % (
                                            st.difference, st.journal_id.amount_authorized_diff))
                if st.journal_id.type not in ['bank', 'cash']:
                    raise UserError(_("The type of the journal for your payment method should be bank or cash "))

                # custom code mario ardi
                if st.journal_id.is_officer_check or st.journal_id.is_department_expense:
                    st.with_context(ctx, order_with_same_journal_id=order_with_same_journal_id,
                                    start_date=start_date).sudo().button_confirm_bank_kg_dept_officer()
                    self.create_additional_journal(st, order_with_same_journal_id)
                else:
                    st.with_context(ctx, order_with_same_journal_id=order_with_same_journal_id,
                                    start_date=start_date).sudo().button_confirm_bank()
                # end of custom code mario ardi

        self.with_context(ctx, start_date=start_date)._confirm_orders()
        self.write({'state': 'closed'})
        return {
            'type': 'ir.actions.client',
            'name': 'Point of Sale Menu',
            'tag': 'reload',
            'params': {'menu_id': self.env.ref('point_of_sale.menu_point_root').id},
        }

    @api.multi
    def create_additional_journal(self, st, order_ids):
        data = []
        for order in order_ids:

            # move_id = order.account_move.id

            for line in order.lines:
                income_account = False
                if line.product_id.property_account_income_id.id:
                    income_account = line.product_id.property_account_income_id.id
                elif line.product_id.categ_id.property_account_income_categ_id.id:
                    income_account = line.product_id.categ_id.property_account_income_categ_id.id

                if not income_account:
                    raise UserError(
                            _('There is no Income Account defined for this product: "%s" -- product category: "%s"') %
                            (line.product_id.name, line.product_id.categ_id.name))
                expense_account = False
                if line.product_id.property_account_expense_id.id:
                    expense_account = line.product_id.property_account_expense_id.id
                elif line.product_id.categ_id.property_account_expense_categ_id.id:
                    expense_account = line.product_id.categ_id.property_account_expense_categ_id.id

                if not expense_account:
                    raise UserError(
                            _('There is no Expense Account defined for this product: "%s" -- product category: "%s"') %
                            (line.product_id.name, line.product_id.categ_id.name))

                # misc_journal_id = self.env['account.journal'].search([
                #     ('company_id.id','=',order.company_id.id),
                #     ('type','=','general'),
                #     ],limit=1)

                # if not misc_journal_id:
                #     raise UserError(
                #         _('There is no Miscellaneous journal defined for this company "%s"') %
                #         (order.company_id.name,))

                cost_price = line.qty * line.product_id.standard_price

                # debit_line = order.account_move.line_ids.with_context(
                #     check_move_validity=False).create({
                #         # 'move_id': move_id,
                #         'name': order.name + ' : ' + line.product_id.name,
                #         'journal_id': st.journal_id.id,
                #         # 'journal_id'    : misc_journal_id.id,
                #         'date': self.working_date,
                #         'account_id': income_account,
                #         'debit': cost_price,
                #         'credit': 0,
                #         # 'statement_id': st.id,
                #         # 'statement_line_id': order.statement_ids[0].id,
                #         # 'payment_id': order.statement_ids[0].journal_entry_ids[0].payment_id.id,
                #     })

                debit_line_vals = (0, 0, {
                    'name': order.name + ' : ' + line.product_id.name,
                    'journal_id': st.journal_id.id,
                    # 'journal_id'    : misc_journal_id.id,
                    'date': self.working_date,
                    'account_id': income_account,
                    'debit': cost_price,
                    'credit': 0,
                    'statement_id': st.id,
                    'statement_line_id': order.statement_ids[0].id,
                    'payment_id': order.statement_ids[0].journal_entry_ids[0].payment_id.id,
                })
                data.append(debit_line_vals)

                credit_line_vals = (0, 0, {
                    'name': order.name + ' : ' + line.product_id.name,
                    'journal_id': st.journal_id.id,
                    # 'journal_id'    : misc_journal_id.id,
                    'date': self.working_date,
                    'account_id': expense_account,
                    'debit': 0,
                    'credit': cost_price,
                    'statement_id': st.id,
                    'statement_line_id': order.statement_ids[0].id,
                    'payment_id': order.statement_ids[0].journal_entry_ids[0].payment_id.id,
                })
                data.append(credit_line_vals)

        move_id = self.env['account.move'].create({
            'ref': self.name + ' - Additional - Internal Transaction',
            'journal_id': st.journal_id.id,
            'date': self.working_date,
            'narration': 'Journal Tambahan - transaksi internal - POS - officer check/dept expense',
            'line_ids': data
        })
        move_id.post()


