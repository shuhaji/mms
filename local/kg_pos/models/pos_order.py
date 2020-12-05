# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
import logging

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class KGPOSOrder(models.Model):
    _inherit = 'pos.order'
    _order = 'id desc'

    def _default_session(self):
        return self.env['pos.session'].search([('state', '=', 'opened'), ('user_id', '=', self.env.uid)], limit=1)

    outlet_id = fields.Many2one('pos.category', 'Outlet', required=False,
                                states={'draft': [('readonly', False)]},
                                readonly=[('state', 'not in', ['draft'])]
                                )
    print_counter_name = fields.Char('Name After Print')

    print_counter = fields.Float(
        'Print Counter',
        default=0,
        digits=dp.get_precision('counter'),
    )

    meal_time_id = fields.Many2one(
        'meal.time',
        'Meal Time',
    )

    meal_time_line_id = fields.Many2one(
        'meal.time.line',
        'Meal Time',
    )

    no_reference = fields.Char(
        'Reference Number'
    )

    is_hotel_guest = fields.Boolean(
        'Is hotel guest',
        default=True,
    )

    department_id = fields.Many2one(
        'hr.department',
        'Departement',
    )

    employee_id = fields.Many2one(
        'hr.employee',
        'Employee',
    )

    customer_id = fields.Many2one(
        'res.partner',
        'Customer',
    )

    change = fields.Float(
        'Change',
        digits=0,
    )

    folio_id = fields.Char('Folio ID')

    room_number = fields.Char('Room Number')

    is_adv_payment = fields.Boolean(
        'Is Advance Payment',
    )

    pos_advance_payment_ids = fields.One2many(
        'pos.advance.payment', 
        'pos_order_id',
        'Advance Payments',
    )

    DepositId = fields.Integer(
        'PMS Adv. Deposit ID',
    )

    waiter_id = fields.Many2one(
        'hr.employee',
        'Waiter',
    )

    working_date = fields.Date(
        related='session_id.working_date',
        string='Working Date', readonly=True)

    pos_tax_ids = fields.One2many(
        'pos.order.tax',
        'pos_order_id',
        'Taxes',
    )

    tax_widget = fields.Text(
        compute='_get_tax_info_JSON',
    )
    
    amount_untaxed = fields.Float(
        compute='_compute_amount_all',
        string='Amount Untaxed (Before Tax and Service)',
        digits=0,
    )
    amount_service = fields.Float(
        compute='_compute_amount_all',
        string='Total Service', digits=0)
    amount_tax_only = fields.Float(
        compute='_compute_amount_all',
        string='Total Tax', digits=0)
    amount_tax = fields.Float(
        compute='_compute_amount_all',
        string='Taxes + Services', digits=0)
    brutto_before_tax = fields.Float(
        compute='_compute_amount_all',
        string='Total Brutto w/o tax', digits=0, store=False)
    total_disc_amount_before_tax = fields.Float(
        compute='_compute_amount_all',
        string='Discount w/o Tax', digits=0, store=False)

    pms_pos_id = fields.Integer("PMS POS Order Id", default=0)

    discount_amount = fields.Float("Discount Amount")
    # discount_by_pct = fields.Float("Discount by percentage")

    @api.depends('statement_ids', 'lines.price_subtotal_incl', 'lines.discount')
    def _compute_amount_all(self):
        for order in self:
            order.amount_paid = order.amount_return = order.amount_tax = 0.0
            currency = order.pricelist_id.currency_id
            order.amount_paid = sum(payment.amount for payment in order.statement_ids)
            order.amount_return = sum(payment.amount < 0 and payment.amount or 0 for payment in order.statement_ids)
            # order.amount_tax = currency.round(sum(self._amount_line_tax(line, order.fiscal_position_id) for line in order.lines))
            amount_untaxed = currency.round(sum(line.price_subtotal for line in order.lines))

            # ditutup by aan, krn amount_tax sudah bisa dihitung dari lines!
            #   (employee_id dan department_id jg sudah dijaga di order lines)
            # # custom code by andi to compute new tax value
            # new_tax_amount = 0.0
            # if order.pos_tax_ids:
            #     if not (order.employee_id or order.department_id):
            #         for tax in order.pos_tax_ids:
            #             new_tax_amount += tax.pos_order_tax_amount
            #             order.amount_tax = new_tax_amount
            #     else:
            #         order.amount_tax = 0.0
            # # end of custom code

            order.brutto_before_tax = currency.round(sum(line.line_brutto_before_tax for line in order.lines))
            order.total_disc_amount_before_tax = currency.round(
                sum(line.line_disc_amount_before_tax for line in order.lines))

            order.amount_untaxed = amount_untaxed
            order.amount_tax = currency.round(sum(line.service_amount + line.tax_amount for line in order.lines))
            order.amount_total = order.amount_tax + order.amount_untaxed
            order.amount_service = currency.round(sum(line.service_amount for line in order.lines))
            order.amount_tax_only = currency.round(sum(line.tax_amount for line in order.lines))

    print_from_button = fields.Boolean(
        'Print From Button',
        default=False,
    )

    coupon_id = fields.Float(
        'Coupon Id',
        default=0.0,
    )
    my_value_id = fields.Char(string="MyValue ID", size=20)
    my_value_name = fields.Char(string="MyValue Name")
    my_value_earn_amount = fields.Float(string="Total Earn Amount", default=0)
    my_value_earn_point = fields.Float(string="Total Earn Point", default=0)
    my_value_earn_status = fields.Selection([
        ('N', 'Not Applicable'),
        ('Y', 'Success'),
        ('E', 'Error'),
    ], string="Send Status")  # null/False/N ==> Not applicable (N ==> pos_config.outlet_id kosong)
    my_value_earn_send_date = fields.Datetime(string="Send Date")
    my_value_earn_error_desc = fields.Char(size=255, string="Error Desc")

    apply_id = fields.Many2one('pos.order', string="Order yg di-refund")

    @api.model
    @api.depends('pos_tax_ids')
    def _get_tax_info_JSON(self):
        self.payments_widget = json.dumps(False)
        if self.pos_tax_ids:
            info = {'title': _('Less Payment'), 'outstanding': False, 'content': self._get_taxes_vals()}
            self.tax_widget = json.dumps(info)

    @api.model
    def _get_taxes_vals(self):
        if not self.pos_tax_ids:
            return []
        tax_vals = []
        
        for tax in self.pos_tax_ids:
            tax_vals.append({
                'name': tax.name, 
                'amount': tax.pos_order_tax_amount,
            })

        return tax_vals

    @api.multi
    def compute_substring_order_number(self):
        for rec in self:
            ref = str(rec.name).split('/')
            rec.order_substring = ref[1]

    @api.one
    def compute_substring_order_number_pos(self, order_number):
        return str(order_number.split('/'))[1]

    def _create_account_move_line(self, session=None, move=None):
        def _flatten_tax_and_children(taxes, group_done=None):
            children = self.env['account.tax']
            if group_done is None:
                group_done = set()
            for tax in taxes.filtered(lambda t: t.amount_type == 'group'):
                if tax.id not in group_done:
                    group_done.add(tax.id)
                    children |= _flatten_tax_and_children(tax.children_tax_ids, group_done)
            return taxes + children

        # Tricky, via the workflow, we only have one id in the ids variable
        """Create a account move line of order grouped by products or not."""
        IrProperty = self.env['ir.property']
        ResPartner = self.env['res.partner']

        if session and not all(session.id == order.session_id.id for order in self):
            raise UserError(_('Selected orders do not have the same session!'))

        grouped_data = {}
        have_to_group_by = session and session.config_id.group_by or False
        rounding_method = session and session.config_id.company_id.tax_calculation_rounding_method

        def add_anglosaxon_lines(grouped_data):
            Product = self.env['product.product']
            Analytic = self.env['account.analytic.account']
            for product_key in list(grouped_data.keys()):
                if product_key[0] == "product":
                    line = grouped_data[product_key][0]
                    product = Product.browse(line['product_id'])
                    # In the SO part, the entries will be inverted by function compute_invoice_totals
                    price_unit = self._get_pos_anglo_saxon_price_unit(product, line['partner_id'], line['quantity'])
                    account_analytic = Analytic.browse(line.get('analytic_account_id'))
                    res = Product._anglo_saxon_sale_move_lines(
                        line['name'], product, product.uom_id, line['quantity'], price_unit,
                            fiscal_position=order.fiscal_position_id,
                            account_analytic=account_analytic)
                    if res:
                        line1, line2 = res
                        line1 = Product._convert_prepared_anglosaxon_line(line1, order.partner_id)
                        insert_data('counter_part', {
                            'name': line1['name'],
                            'account_id': line1['account_id'],
                            'credit': line1['credit'] or 0.0,
                            'debit': line1['debit'] or 0.0,
                            'partner_id': line1['partner_id']

                        })

                        line2 = Product._convert_prepared_anglosaxon_line(line2, order.partner_id)
                        insert_data('counter_part', {
                            'name': line2['name'],
                            'account_id': line2['account_id'],
                            'credit': line2['credit'] or 0.0,
                            'debit': line2['debit'] or 0.0,
                            'partner_id': line2['partner_id']
                        })

        for order in self.filtered(lambda o: not o.account_move or o.state == 'paid'):
            current_company = order.sale_journal.company_id
            account_def = IrProperty.get(
                'property_account_receivable_id', 'res.partner')
            order_account = order.partner_id.property_account_receivable_id.id or account_def and account_def.id
            partner_id = ResPartner._find_accounting_partner(order.partner_id).id or False
            if move is None:
                # Create an entry for the sale
                journal_id = self.env['ir.config_parameter'].sudo().get_param(
                    'pos.closing.journal_id_%s' % current_company.id, default=order.sale_journal.id)
                move = self._create_account_move(
                    order.session_id.start_at, order.name, int(journal_id), order.company_id.id)

            def insert_data(data_type, values):
                # if have_to_group_by:
                values.update({
                    'partner_id': partner_id,
                    'move_id': move.id,
                })

                key = self._get_account_move_line_group_data_type_key(data_type, values, {'rounding_method': rounding_method})
                if not key:
                    return

                grouped_data.setdefault(key, [])

                if have_to_group_by:
                    if not grouped_data[key]:
                        grouped_data[key].append(values)
                    else:
                        current_value = grouped_data[key][0]
                        current_value['quantity'] = current_value.get('quantity', 0.0) + values.get('quantity', 0.0)
                        current_value['credit'] = current_value.get('credit', 0.0) + values.get('credit', 0.0)
                        current_value['debit'] = current_value.get('debit', 0.0) + values.get('debit', 0.0)
                        if key[0] == 'tax' and rounding_method == 'round_globally':
                            if current_value['debit'] - current_value['credit'] > 0:
                                current_value['debit'] = current_value['debit'] - current_value['credit']
                                current_value['credit'] = 0
                            else:
                                current_value['credit'] = current_value['credit'] - current_value['debit']
                                current_value['debit'] = 0

                else:
                    grouped_data[key].append(values)

            # because of the weird way the pos order is written, we need to make sure there is at least one line,
            # because just after the 'for' loop there are references to 'line' and 'income_account' variables (that
            # are set inside the for loop)
            # TOFIX: a deep refactoring of this method (and class!) is needed
            # in order to get rid of this stupid hack
            assert order.lines, _('The POS order must have lines when calling this method')
            # Create an move for each order line
            cur = order.pricelist_id.currency_id

            # CUSTOM CODE = IF NOT ORDER.COUPON_ID
            if not order.coupon_id:
                for line in order.lines:
                    amount = line.price_subtotal

                    # custom code by mas mario
                    if order.department_id or order.employee_id:
                        amount = line.product_id.standard_price * line.qty
                    # end of custom code

                    # Search for the income account
                    if line.product_id.property_account_income_id.id:
                        income_account = line.product_id.property_account_income_id.id
                    elif line.product_id.categ_id.property_account_income_categ_id.id:
                        income_account = line.product_id.categ_id.property_account_income_categ_id.id
                    else:
                        raise UserError(_('Please define income '
                                        'account for this product: "%s" (id:%d).')
                                        % (line.product_id.name, line.product_id.id))

                    name = line.product_id.name
                    if line.notice:
                        # add discount reason in move
                        name = name + ' (' + line.notice + ')'

                    # Create a move for the line for the order line
                    # Just like for invoices, a group of taxes must be present on this base line
                    # As well as its children
                    base_line_tax_ids = _flatten_tax_and_children(line.tax_ids_after_fiscal_position).filtered(lambda tax: tax.type_tax_use in ['sale', 'none'])
                    insert_data('product', {
                        'name': name,
                        'quantity': line.qty,
                        'product_id': line.product_id.id,
                        'account_id': income_account,
                        'analytic_account_id': self._prepare_analytic_account(line),
                        'credit': ((amount > 0) and amount) or 0.0,
                        'debit': ((amount < 0) and -amount) or 0.0,
                        'tax_ids': [(6, 0, base_line_tax_ids.ids)],
                        'partner_id': partner_id
                    })

                    # Create the tax lines
                    taxes = line.tax_ids_after_fiscal_position.filtered(lambda t: t.company_id.id == current_company.id)
                    if not taxes:
                        continue
                    price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    for tax in taxes.compute_all(price, cur, line.qty)['taxes']:
                        insert_data('tax', {
                            'name': _('Tax') + ' ' + tax['name'],
                            'product_id': line.product_id.id,
                            'quantity': line.qty,
                            'account_id': tax['account_id'] or income_account,
                            'credit': ((tax['amount'] > 0) and tax['amount']) or 0.0,
                            'debit': ((tax['amount'] < 0) and -tax['amount']) or 0.0,
                            'tax_line_id': tax['id'],
                            'partner_id': partner_id,
                            'order_id': order.id
                        })
            
            #CUSTOM CODE IF ORDER USED VOUCHER COUPONS
            elif order.coupon_id:
                for line in order.lines:
                    amount = line.price_subtotal

                    # custom code by mas mario
                    if order.department_id or order.employee_id:
                        amount = line.product_id.standard_price * line.qty
                    # end of custom code

                    # Search for the income account
                    if line.product_id.property_account_income_id.id:
                        income_account = line.product_id.property_account_income_id.id
                    elif line.product_id.categ_id.property_account_income_categ_id.id:
                        income_account = line.product_id.categ_id.property_account_income_categ_id.id
                    else:
                        raise UserError(_('Please define income '
                                        'account for this product: "%s" (id:%d).')
                                        % (line.product_id.name, line.product_id.id))

                    name = line.product_id.name
                    if line.notice:
                        # add discount reason in move
                        name = name + ' (' + line.notice + ')'

                    # Create a move for the line for the order line
                    # Just like for invoices, a group of taxes must be present on this base line
                    # As well as its children
                    base_line_tax_ids = _flatten_tax_and_children(line.tax_ids_after_fiscal_position).filtered(lambda tax: tax.type_tax_use in ['sale', 'none'])
                    insert_data('product', {
                        'name': name,
                        'quantity': line.qty,
                        'product_id': line.product_id.id,
                        'account_id': income_account,
                        'analytic_account_id': self._prepare_analytic_account(line),
                        'credit': ((amount > 0) and amount) or 0.0,
                        'debit': ((amount < 0) and -amount) or 0.0,
                        'tax_ids': [(6, 0, base_line_tax_ids.ids)],
                        'partner_id': partner_id
                    })
                for tax in order.pos_tax_ids:
                    real_tax_id = int(tax.real_tax_id) or False
                    if not real_tax_id:
                        continue
                    real_tax = self.env['account.tax'].browse(real_tax_id)
                    insert_data('tax', {
                        'name': _('Tax') + ' ' + tax.name,
                        'product_id': False,
                        'quantity': 1,
                        'account_id': real_tax.account_id.id or income_account,
                        'credit': ((tax.pos_order_tax_amount > 0) and tax.pos_order_tax_amount) or 0.0,
                        'debit': ((tax.pos_order_tax_amount < 0) and -tax.pos_order_tax_amount) or 0.0,
                        'tax_line_id': real_tax.id,
                        'partner_id': partner_id,
                        'order_id': order.id
                    })
                    


            # round tax lines per order
            if rounding_method == 'round_globally':
                for group_key, group_value in grouped_data.items():
                    if group_key[0] == 'tax':
                        for line in group_value:
                            line['credit'] = cur.round(line['credit'])
                            line['debit'] = cur.round(line['debit'])

            # custom code by mas mario
            # counterpart
            counterpart_amount = order.amount_total

            if order.department_id or order.employee_id:
                counterpart_amount = 0
                for ord_pos in order.lines:
                    counterpart_amount += ord_pos.product_id.standard_price * ord_pos.qty

            insert_data('counter_part', {
                'name': _("Trade Receivables"),  # order.name,
                'account_id': order_account,
                # 'credit': ((order.amount_total < 0) and -order.amount_total) or 0.0,
                # 'debit': ((order.amount_total > 0) and order.amount_total) or 0.0,
                'credit': ((counterpart_amount < 0) and -counterpart_amount) or 0.0,
                'debit': ((counterpart_amount > 0) and counterpart_amount) or 0.0,
                'partner_id': partner_id
            })
            # end of custom code

            # original code
            # counterpart
            # insert_data('counter_part', {
            #     'name': _("Trade Receivables"),  # order.name,
            #     'account_id': order_account,
            #     'credit': ((order.amount_total < 0) and -order.amount_total) or 0.0,
            #     'debit': ((order.amount_total > 0) and order.amount_total) or 0.0,
            #     'partner_id': partner_id
            # })
            # end of original code

            order.write({'state': 'done', 'account_move': move.id})

        if self and order.company_id.anglo_saxon_accounting:
            add_anglosaxon_lines(grouped_data)

        all_lines = []
        for group_key, group_data in grouped_data.items():
            for value in group_data:
                all_lines.append((0, 0, value),)

        if move:  # In case no order was changed
            move.sudo().write({'line_ids': all_lines})

            # custom code
            for lines in move.line_ids:
                lines.write ({
                    # 'date_maturity': self.env.context.get('start_date', False)
                    'date': self.env.context.get('start_date', False)
                })
            # end of custom code
            
            move.sudo().post()
        return True

    @api.multi
    def print_report(self):
        if 'REFUND' in self.lines.mapped('name')[0]:
            payment_amount = sum(line.amount for line in self.statement_ids) - (self.amount_total)
            change = payment_amount
        else:
            payment_amount = self.statement_ids.filtered(lambda line:
                (
                line.amount > 0
                )
            ).mapped('amount')
            total_payment_amount = sum(amount for amount in payment_amount)
            total_order_amount = sum(line.price_subtotal_incl for line in self.lines)

            if self.change != 0:
                change = self.change
            else:
                change = total_payment_amount - total_order_amount

        pos_order_rec = self
        data = {
            'ids': pos_order_rec.ids,
            'model': pos_order_rec,
            'model_name': pos_order_rec._name,
            'change': change,
        }

        self.print_counter += 1

        self.write({
            'print_counter_name': '%s - duplicate %d' % (self.name, self.print_counter)
        })

        return self.env.ref('kg_pos.kg_pos_order_report_action').with_context(print_from_button = True).report_action(self, data=data)

    @api.multi
    def print_restaurant_bill_report(self):
        self.print_counter += 1
        self.print_from_button = True
        self.write({
            'print_counter_name': '%s - duplicate %d' % (self.name, self.print_counter)
        })
        return self.env.ref('kg_pos.kg_pos_restaurant_bill_report_action').report_action(self) 

    @api.model
    def _process_order(self, pos_order):
        order = super(KGPOSOrder,self)._process_order(pos_order)
        # custom code used when we want to get all taxes from pos and their amount used in pos order
        if pos_order.get('list_of_taxes', False):
            for taxes in pos_order.get('list_of_taxes', False):      
                values = (0, 0, {
                    'name': taxes.get('tax_name', ''),
                    'pos_order_tax_amount': taxes.get('tax_amount', 0.0),
                    'real_tax_id': taxes.get('tax_id', 0.0),
                })
                order.pos_tax_ids = [values]
        # end of custom code

        # custom code for sending data to PMS when there is charge to room payment method
        if (int(order.room_number) and int(order.folio_id)) > 0:
            order.pms_pos_id = self.env['pos.helpers'].post_payment(order)

        # custom code by andi for adv_payment feature
        used_adv_payment = pos_order.get('used_adv_payment', False)
        if used_adv_payment:
            order.write({
                'is_adv_payment': True,
                'partner_id': pos_order.get('adv_payment_partner', False),
            })
            for payment in used_adv_payment:
                # adv_payment_date = datetime.strptime(order.date_order, '%Y-%m-%d %H:%M:%S').date()
                adv_payment_date = order.session_id.working_date

                residual = payment.get('payment_residual', 0)
                # if payment['full_used_adv_payment']:
                #     residual = payment['current_adv_payment']['residual'] - payment['adv_payment_amount_used']
                    
                values = (0, 0, {
                    'adv_payment_id': payment['current_adv_payment']['id'],
                    'payment_date': adv_payment_date,
                    'name': payment['current_adv_payment']['name'],
                    'journal_id': payment['current_adv_payment']['journal_id'][0],
                    'deposit_type': payment['current_adv_payment'].get('deposit_type_id', False),
                    'partner_id': payment['current_adv_payment']['partner_id'][0],
                    'amount': payment['current_adv_payment']['amount'],
                    'new_residual': residual,
                    'state': payment['current_adv_payment']['state'],
                    'company_id': payment['current_adv_payment']['company_id'][0],
                    'is_advance_payment': payment['current_adv_payment']['is_advance_payment'],
                    'payment_type': payment['current_adv_payment']['payment_type'],
                    'payment_method_id': payment['current_adv_payment']['payment_method_id'][0],
                    'currency_id': payment['current_adv_payment']['currency_id'][0],
                    'advance_payment_account_id': payment['current_adv_payment']['advance_payment_account_id'][0],
                    'adv_payment_amount_used': payment['adv_payment_amount_used'],
                    
                })

                order.pos_advance_payment_ids = [values]
                amount_used = payment['adv_payment_amount_used']
                adv_payment_id = int(payment['current_adv_payment']['id'])

                self.update_advance_payment_residual_amount(adv_payment_id, amount_used)
        # end of custom code

        # custom code for adding waiter
        if pos_order.get('waiter', False):
            order.waiter_id = pos_order.get('waiter',False).get('id', False)
        # end of custom code

        # custom code for applying my value redeem or earn point
        # is_point_journal = order.mapped('statement_ids').mapped('journal_id').filtered(lambda journal: journal.is_point)
        # if order.amount_total == pos_order.get('my_value_points_used', 0.0):
        #     #REDEEM POINTS WHEN USED REDEEM POINT VALUE IS SAME AS ORDER. AMOUNT TOTAL
        #     if pos_order.get('my_value_points_used', False):
        #         my_value_data = pos_order.get('my_value_data', False)
        #         my_value_points = pos_order.get('my_value_points', 0.0)
        #         my_value_points_used = pos_order.get('my_value_points_used', 0.0)
                
        #         # self.env['pos.helpers'].send_redeem_points(my_value_data, my_value_points, my_value_points_used, order)
        # else:
        #     # EARN POINT
        #     if pos_order.get('my_value_data', False):
        #         my_value_data = pos_order.get('my_value_data', False)
        #         my_value_points = pos_order.get('my_value_points', 0.0)
        #         my_value_points_used = pos_order.get('my_value_points_used', 0.0)
            
        #         # self.env['pos.helpers'].send_earn_points(my_value_data, my_value_points, my_value_points_used, order)

        #     # REDEEM POINT
        #     if pos_order.get('my_value_points_used', False):
        #         my_value_data = pos_order.get('my_value_data', False)
        #         my_value_points = pos_order.get('my_value_points', 0.0)
        #         my_value_points_used = pos_order.get('my_value_points_used', 0.0)
                
        #         # self.env['pos.helpers'].send_redeem_points(my_value_data, my_value_points, my_value_points_used, order)
        # end of custom code

        # custom code for to change the value of order amount total to make the order in paid state (can return true in function test_paid())
        if pos_order.get('coupon_id', False):
            order.amount_total = order.amount_paid
        # end of custom code

        return order

    def update_advance_payment_residual_amount(self, adv_payment_id, amount_used):
        # Update the residual of used advance payment
        query = """UPDATE account_payment SET residual_temp = residual_temp - {amount_used}, 
            residual = residual - {amount_used}
            WHERE id = {adv_payment_id}"""
        final_query = query.format(amount_used=amount_used, adv_payment_id=adv_payment_id)
        self.env.cr.execute(final_query)
        # real_advance_payment = self.env['account.payment'].search(
        #   [('id', '=', payment['current_adv_payment']['id'])])
        # real_advance_payment.write({
        #     'residual_temp': residual,
        #     # code for the real residual of current adv payment, if someday needed
        #     'residual': residual,
        #     # end of code
        # })

    def _prepare_bank_statement_line_payment_values(self, data):
        res = super(KGPOSOrder, self)._prepare_bank_statement_line_payment_values(data)
        if self.department_id.allow_pos_expense:
            res['amount'] = self.amount_total
        if self.employee_id.is_officer_check:
            res['amount'] = self.amount_total
        # if self.customer_id.allow_use_city_ledger:
        #     res['amount'] = self.amount_total
        return res

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(KGPOSOrder, self)._order_fields(ui_order)

        # add coupon id and voucher coupon value if voucher is applied in order
        if ui_order.get('coupon_id', 0.0):
            order_fields['coupon_id'] = ui_order.get('coupon_id', 0.0)

        order_fields['outlet_id'] = ui_order.get('outlet_id', False)
        # end of custom code

        order_fields['meal_time_line_id'] = ui_order.get('meal_time_line_id', False)
        order_fields['no_reference'] = ui_order.get('no_reference', '')
        order_fields['is_hotel_guest'] = ui_order.get('is_hotel_guest', True)
        order_fields['change'] = ui_order.get('change', 0)
        order_fields['folio_id'] = ui_order.get('folio_id', 0)
        order_fields['room_number'] = ui_order.get('room_number', 0)
        if isinstance(ui_order.get('department_id'), dict) :
            order_fields['department_id'] = ui_order['department_id']['id'] or False
            for lines in order_fields['lines']:
                lines[2]['tax_ids'] = False
        if isinstance(ui_order.get('employee_id'), dict) :
            order_fields['employee_id'] = ui_order['employee_id']['id'] or False
            for lines in order_fields['lines']:
                lines[2]['tax_ids'] = False
        if isinstance(ui_order.get('customer_id'), dict) :
            order_fields['customer_id'] = ui_order['customer_id']['id'] or False

        order_fields['my_value_id'] = ui_order.get('my_value_id', False)
        order_fields['my_value_name'] = ui_order.get('my_value_name', False)
        order_fields['my_value_earn_status'] = ui_order.get('my_value_earn_status', False)
        order_fields['my_value_earn_amount'] = ui_order.get('my_value_earn_amount', 0)
        order_fields['my_value_earn_point'] = ui_order.get('my_value_earn_point', 0)

        order_fields['my_value_earn_send_date'] = ui_order.get('my_value_earn_send_date', False)
        order_fields['my_value_earn_error_desc'] = ui_order.get('my_value_earn_error_desc', False)

        order_fields['discount_amount'] = ui_order.get('discount_amount', False)

        return order_fields

    def _payment_fields(self, ui_paymentline):
        payments = super(KGPOSOrder, self)._payment_fields(ui_paymentline)
        payments['voucher_id'] = ui_paymentline.get('voucher_id', False)
        payments['voucher_no'] = ui_paymentline.get('voucher_no', False)
        if ui_paymentline.get('issuer_type', False) \
                or ui_paymentline.get('card_holder_name', '') or ui_paymentline.get('front_card_number', '') \
                or ui_paymentline.get('back_card_number', ''):
            payments['issuer_type_id'] = ui_paymentline.get('issuer_type', False)
            payments['card_holder_name'] = ui_paymentline.get('card_holder_name', False)
            payments['card_number'] = '%s - xxxx - xxxx - %s' % (
                ui_paymentline.get('front_card_number', ''), ui_paymentline.get('back_card_number', ''))
        return payments

    def _prepare_bank_statement_line_payment_values(self, data):
        args = super(KGPOSOrder, self)._prepare_bank_statement_line_payment_values(data)
        args.update({
            'issuer_type_id': data.get('issuer_type_id'),
            'card_holder_name': data.get('card_holder_name'),
            'card_number': data.get('card_number'),
            'voucher_id': data.get('voucher_id'),
            'voucher_no': data.get('voucher_no'),
        })
        return args

    @api.multi
    def refund(self):
        """Create a copy of order  for refund order"""
        PosOrder = self.env['pos.order']
        for order in self:

            current_session = self.env['pos.session'].search(
                [('state', '!=', 'closed'),
                 ('config_id', '=', order.config_id.id),
                 ('working_date', '=', order.working_date),
                 ('user_id', '=', self.env.uid)],
                limit=1)
            if not current_session:
                raise UserError(
                    _('To return products, you must open a POS session with the same outlet and working date'))

            if order.my_value_earn_amount != 0:
                raise UserError(
                    _('This order have earning point, return not allowed.'))

            for line in order.statement_ids:
                if line.journal_id.is_charge_room:
                    order.refund_order_charge_to_room()
                if line.journal_id.is_point:
                    raise UserError(
                        _('You are not allow to return product(s) on order with point payment.'))
                if line.journal_id.is_city_ledger:
                    if order.invoice_id:
                        if order.invoice_id.state != 'open' or order.invoice_id.amount_total - order.invoice_id.residual != 0:
                            raise UserError(
                                _('To return products, invoice status must be open and no payment has been made for the invoice'))

            clone = order.copy({
                # not used, name forced by create
                'name': order.name + _(' REFUND'),
                'session_id': current_session.id,
                'date_order': fields.Datetime.now(),
                'pos_reference': order.pos_reference,
                'apply_id': order.id,
                'lines': False,
            })
            for line in order.lines:
                clone_line = line.copy({
                    # required=True, copy=False
                    'name': line.name + _(' REFUND'),
                    'order_id': clone.id,
                    'qty': -line.qty,
                })
            # create payment, copy from order
            for payment_line in order.statement_ids:
                # find statement in current session with the same journal id
                for current_statement in current_session.statement_ids:
                    if payment_line.journal_id.id == current_statement.journal_id.id:
                        clone_payment_line = payment_line.copy({
                            'statement_id': current_statement.id,
                            'amount': payment_line.amount * -1,
                            'date': current_session.working_date,
                            'pos_statement_id': clone.id
                        })
            clone.action_pos_order_paid()
            for advance_payment in order.pos_advance_payment_ids:
                clone_advance_payment = advance_payment.copy({
                    'name': advance_payment.name + _(' REFUND'),
                    'pos_order_id': clone.id,
                    'adv_payment_amount_used': -advance_payment.adv_payment_amount_used,
                    'new_residual': advance_payment.new_residual + advance_payment.adv_payment_amount_used
                })
                amount_used = -advance_payment.adv_payment_amount_used
                adv_payment_id = advance_payment.adv_payment_id
                self.update_advance_payment_residual_amount(adv_payment_id, amount_used)
            PosOrder += clone

        return {
            'name': _('Return Products'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.order',
            'res_id': PosOrder.ids[0],
            'view_id': False,
            'context': self.env.context,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    @api.model
    def post_refund_order_advance_payment(self):
        # order = order yg di return
        if self.apply_id.pos_advance_payment_ids:
            # Cancel Invoice & alokasi advance deposit atas order yang diretur atau refund
            if self.apply_id and self.apply_id.invoice_id and \
                    self.apply_id.invoice_id.advance_payment_ids:
                advance_payments = self.apply_id.invoice_id.advance_payment_ids
                for adv_deposit in advance_payments:
                    self.apply_id.invoice_id.cancel_applied_payment(
                        payment_id=adv_deposit.id,
                        invoice_id=self.apply_id.invoice_id.id)
                self.apply_id.invoice_id.action_invoice_cancel()
                # code for sending data to PMS, update balance on pms
                post_request = self.env['pos.helpers']
                post_request.post_adv_payment(advance_payments=advance_payments)
                # end of code

    def post_refund_order_city_ledger(self):
        for retur in self:
            order = retur.apply_id
            if order:
                for statement in order.statement_ids:
                    if statement.journal_id.is_city_ledger:
                        invoice = order.invoice_id
                        invoice_refund = self.env['account.invoice.refund'].with_context(active_ids=invoice.id).create({
                            'date_invoice': retur.session_id.working_date,
                            'date': retur.session_id.working_date,
                            'description': 'Refund POS Order City Ledger',
                            # 'refund_only': False,
                            'filter_refund': 'cancel',
                        })
                        # invoice_refund.filter_refund = 'cancel'
                        result = invoice_refund.invoice_refund()
                        return result

    def refund_order_charge_to_room(self):
        post_request = self.env['pos.helpers']

        messages = post_request.get_return_charge_to_room(self)

        if messages.status_code == 200:
            return
        else:
            message = 'Failed to refund POS.'
            json_response = messages.json()
            msg = json_response.get("Message")

            raise UserError(message + '\n' + msg + '\n' + 'Status Code' + " " + str(messages.status_code))


class KGPOSOrderReport(models.AbstractModel):
    _name = 'report.kg_pos.kg_pos_order_report'

    @api.multi
    def get_report_values(self, docids, data=None):
        if data:
            ids = data['ids']
            report_model = self.env[data['model_name']].browse(ids)
            change = data.get('change', 0.0)
            # report_model.product_id['price_after_disc'] = data['data']['price_after_disc']
            docargs = {
                'doc_ids': report_model.ids,
                'doc_model': data['context']['active_model'],
                'docs': report_model,
                'change': change,
            }
            return docargs


class KGPOSAdvancePayment(models.Model):
    _name = 'pos.advance.payment'
    _inherit = 'account.payment'

    adv_payment_id = fields.Float(
        'Advance Payment_id'
    )

    new_residual = fields.Float(
        'Remaining Amount',
        readonly=True,
        default=0.0,
    )

    adv_payment_amount_used = fields.Float(
        'Advance Payment Amount Used',
        default=0.0,
    )

    pos_order_id = fields.Many2one(
        'pos.order',
        'POS Order',
    )


class KGPOSOrderLine(models.Model):
    _inherit = 'pos.order.line'

    # custom aan: store subtotal to db
    #   for easier and faster report generation and data extraction (analytics)!
    price_subtotal = fields.Float(compute='_compute_amount_line_all', digits=0,
                                  string='Subtotal w/o Tax', store=True)
    #   subtotal include tax and services
    price_subtotal_incl = fields.Float(compute='_compute_amount_line_all', digits=0,
                                       string='Subtotal', store=True)
    #   subtotal service amount only
    service_amount = fields.Float(compute='_compute_amount_line_all', digits=0, string='Service Amount', store=True)
    #   subtotal tax amount only
    tax_amount = fields.Float(compute='_compute_amount_line_all', digits=0, string='Tax Amount', store=True)

    line_brutto_before_tax = fields.Float(
        compute='_compute_amount_line_all', digits=0,
        string='Brutto w/o Tax', store=False)
    line_disc_amount_before_tax = fields.Float(
        compute='_compute_amount_line_all', digits=0,
        string='Discount w/o Tax', store=False)

    @api.depends('price_unit', 'tax_ids', 'qty', 'discount', 'discount_amount', 'product_id')
    def _compute_amount_line_all(self):
        for line in self:
            fpos = line.order_id.fiscal_position_id
            tax_ids_after_fiscal_position = fpos.map_tax(
                line.tax_ids, line.product_id, line.order_id.partner_id) if fpos else line.tax_ids

            if line.order_id.discount_amount:
                # discount by amount
                discount_amount = line.discount_amount
            else:
                # discount by percent
                discount_amount = (1 - (line.discount or 0.0) / 100.0)

            price = line.price_unit * discount_amount
            taxes = tax_ids_after_fiscal_position.compute_all(
                price, line.order_id.pricelist_id.currency_id, line.qty,
                product=line.product_id, partner=line.order_id.partner_id)

            # modification: by aan,
            if line.order_id.employee_id or line.order_id.department_id:
                # tax and service not applied for internal transactions
                amount_with_tax = taxes['total_excluded']
                service_amount = 0
            else:
                amount_with_tax = taxes['total_included']
                service_amount = taxes['total_service_amount']

            line_net_before_tax = taxes['total_excluded']
            line_brutto_before_tax = (line_net_before_tax * 100) / (100 - (line.discount or 0.0))
            line_disc_amount_before_tax = line_brutto_before_tax - line_net_before_tax

            line.update({
                'price_subtotal_incl': amount_with_tax,
                'price_subtotal': taxes['total_excluded'],
                'service_amount': service_amount,
                'tax_amount': amount_with_tax - taxes['total_excluded'] - service_amount,
                'line_brutto_before_tax': line_brutto_before_tax,
                'line_disc_amount_before_tax': line_disc_amount_before_tax,
                'discount_amount': discount_amount
            })

    custom_item_name = fields.Char(
        'Custom Item Name'
    )

    discount_amount = fields.Float("Discount Amount", digits=0, default=0.0)
    discount = fields.Float(string='Discount (%)', digits=0, default=0.0)

    note = fields.Char(
        'Custom Note'
    )

    @api.model
    def create(self, values):
        if values.get('order_id') and not values.get('name'):
            # set name based on the sequence specified on the config
            config_id = self.order_id.browse(values['order_id']).session_id.config_id.id
            # HACK: sequence created in the same transaction as the config
            # cf TODO master is pos.config create
            # remove me saas-15

            # custom code
            if not config_id:
                config_id = self.order_id.browse(values['order_id']).reservation_pos_id.id
            # end of code

            self.env.cr.execute("""
                SELECT s.id
                FROM ir_sequence s
                JOIN pos_config c
                  ON s.create_date=c.create_date
                WHERE c.id = %s
                  AND s.code = 'pos.order.line'
                LIMIT 1
                """, (config_id,))
            sequence = self.env.cr.fetchone()
            if sequence:
                values['name'] = self.env['ir.sequence'].browse(sequence[0])._next()
        if not values.get('name'):
            # fallback on any pos.order sequence
            values['name'] = self.env['ir.sequence'].next_by_code('pos.order.line')
        return super(KGPOSOrderLine, self).create(values)


class KGAccountTax(models.Model):
    _name = 'pos.order.tax'

    name = fields.Char(
        'Name',
    )

    pos_order_id = fields.Many2one(
        'pos.order', 
        'POS Order',
    )

    pos_order_tax_amount = fields.Float(
        'POS Order Tax Amount',
        default=0.0,
    )

    real_tax_id = fields.Float(
        'Real Tax ID',
    )