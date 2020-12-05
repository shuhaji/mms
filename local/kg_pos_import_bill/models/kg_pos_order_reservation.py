# -*- coding: utf-8 -*-

from odoo import models, api, fields, _
from odoo.exceptions import except_orm, Warning, RedirectWarning, UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.addons import decimal_precision as dp
import pytz
from datetime import datetime, timedelta
import random
import string


class KgPosOrder(models.Model):
    _inherit = 'pos.order'

    is_reservation = fields.Boolean('Is Reservation', default=False)
    reservation_order_id = fields.Many2one('kg.pos.order.reservation', 'pos_order_id')

    # TODO: saat order sudah di posted sessionnya.. pastikan jg mencheckout reservationnya
    @api.model
    def _process_order(self, pos_order):
        order = super(KgPosOrder, self)._process_order(pos_order)
        if order.reservation_order_id:
            if order.reservation_order_id.state_reservation not in ('check_out', 'cancel'):
                order.reservation_order_id.state_reservation = 'check_out'
        return order

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(KgPosOrder, self)._order_fields(ui_order)
        order_fields['is_reservation'] = ui_order.get('is_reservation', False)
        order_fields['reservation_order_id'] = ui_order.get('reservation_order_id', False)
        return order_fields


class KgPosOrderReservation(models.Model):
    _name = 'kg.pos.order.reservation'
    # _inherit = 'pos.order'  # removed inheritence, upgrade problem with kg pos when there r new fields in kg pos order
    # _order = 'reservation_time_start asc, name asc'
    _order = "id desc"

    reservation_pos_id = fields.Many2one(
        comodel_name='pos.config', string='Point of Sales', required=False)

    session_id = fields.Many2one(
        'pos.session', string='Session', required=False, index=True,
        domain="[('state', '=', 'opened')]", states={'draft': [('readonly', False)]},
        readonly=False)

    pos_orders = fields.One2many('pos.order', 'reservation_order_id', 'POS Orders')
    lines = fields.One2many('kg.pos.order.reservation.line', 'order_id', string='List Products',
                            states={'draft': [('readonly', False)]},
                            readonly=True, copy=True)
    is_reservation = fields.Boolean('Is Reservation', default=False)

    # <editor-fold desc="Fields copied from pos order">
    name = fields.Char(string='Order Ref', required=True, readonly=True, copy=False, default='/')
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True,
                                 default=lambda self: self.env.user.company_id)
    date_order = fields.Datetime(string='Order Date', readonly=True, index=True, default=fields.Datetime.now)
    user_id = fields.Many2one(
        comodel_name='res.users', string='Salesman',
        help="Person who uses the cash register. It can be a reliever, a student or an interim employee.",
        default=lambda self: self.env.uid,
        states={'done': [('readonly', True)], 'invoiced': [('readonly', True)]},
    )

    statement_ids = fields.One2many('account.bank.statement.line', 'pos_statement_id', string='Payments',
                                    states={'draft': [('readonly', False)]}, readonly=True)

    pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist',
        required=False,  # original pos order: required = True, here it's false
        states={'draft': [('readonly', False)]}
    )

    partner_id = fields.Many2one('res.partner', string='Customer', change_default=True, index=True,
                                 states={'draft': [('readonly', False)], 'paid': [('readonly', False)]})
    sequence_number = fields.Integer(string='Sequence Number', help='A session-unique sequence number for the order',
                                     default=1)

    state = fields.Selection(
        [('draft', 'New'), ('cancel', 'Cancelled'), ('paid', 'Paid'), ('done', 'Posted'), ('invoiced', 'Invoiced')],
        'Status', readonly=True, copy=False, default='draft')

    invoice_id = fields.Many2one('account.invoice', string='Invoice', copy=False)
    account_move = fields.Many2one('account.move', string='Journal Entry', readonly=True, copy=False)
    picking_id = fields.Many2one('stock.picking', string='Picking', readonly=True, copy=False)
    picking_type_id = fields.Many2one('stock.picking.type', related='session_id.config_id.picking_type_id',
                                      string="Operation Type")
    location_id = fields.Many2one(
        comodel_name='stock.location',
        related='session_id.config_id.stock_location_id',
        string="Location", store=True,
        readonly=True,
    )
    note = fields.Text(string='Internal Notes')
    nb_print = fields.Integer(string='Number of Print', readonly=True, copy=False, default=0)
    pos_reference = fields.Char(string='Receipt Ref', readonly=True, copy=False)
    sale_journal = fields.Many2one('account.journal', related='session_id.config_id.journal_id', string='Sales Journal',
                                   store=True, readonly=True)
    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position', string='Fiscal Position',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    @api.multi
    def unlink(self):
        for pos_order in self.filtered(lambda pos_order: pos_order.state not in ['draft', 'cancel']):
            raise UserError(_('In order to delete a sale, it must be new or cancelled.'))
        return super(KgPosOrderReservation, self).unlink()

    table_id = fields.Many2one('restaurant.table', string='Table', help='The table where this order was served')
    customer_count = fields.Integer(string='Guests', help='The amount of customers that have been served by this order.')
    # </editor-fold>

    # <editor-fold desc="Fields specific for pos order table reservation">
    # is_reservation = fields.Boolean('Is Reservation', default=True)
    # reservation_time_start      = fields.Datetime('Reservation Time Start', default=fields.Datetime.now())
    # reservation_time_end        = fields.Datetime('Reservation Time End', default=fields.Datetime.now())
    reservation_time_start = fields.Datetime('Reservation Time Start')
    reservation_time_end = fields.Datetime('Reservation Time End')
    company_name = fields.Many2one('res.partner', 'Customer/Company')
    booking_phone_number = fields.Char('Booking Phone Number')
    reserved_by = fields.Char('Reserved by')
    event_type_id = fields.Many2one('catalog.eventtype', 'Event Type')
    event_name = fields.Char('Event Name')
    state_reservation = fields.Selection([
        ('tentative', 'Tentative'),
        ('waiting_list', 'Waiting List'),
        ('definite', 'Definite'),
        ('check_in', 'Check-In'),
        ('check_out', 'Check-Out'),
        ('cancel', 'Cancel')
    ], string='Reservation Status')
    cancel_reason = fields.Text('Cancel Reason', readonly=True)
    cancel_time = fields.Datetime(string='Cancel on', readonly=True)
    cancel_by = fields.Many2one(comodel_name='res.users', string='Cancel by', readonly=True)
    salesperson_id = fields.Many2one(comodel_name='hr.employee', string='Salesperson')
    table_list = fields.One2many(comodel_name='kg.pos.order.reservation.table',
                                 inverse_name='reservation_id', string='Table List',
                                 required=True)

    order_substring = fields.Char(string='Order Number', compute='compute_substring_order_number', store=False)
    amount_tax_table = fields.Float(string='Amount Tax', compute='compute_amount_tax_table', store=True)
    table_label = fields.Char(string='Table Label', compute='compute_table_list', store=True)
    date_order_tz = fields.Datetime(string='Date Order', compute='compute_date_order_tz', store=False)
    start_time_tz = fields.Char(string='Start Time', compute='compute_time_tz', store=False)
    end_time_tz = fields.Char(string='End Time', compute='compute_time_tz', store=False)
    reservation_start_date = fields.Char(string='Reservation Start Date', compute='compute_time_tz', store=False)

    # </editor-fold>

    @api.onchange('reservation_pos_id')
    def onchange_pricelist_id(self):
        if self.reservation_pos_id:
            self.pricelist_id = self.reservation_pos_id.pricelist_id
            self.fiscal_position_id = self.reservation_pos_id.default_fiscal_position_id

    amount_total = fields.Float(compute='_compute_amount_all', string='Total', digits=0)
    amount_paid = fields.Float(compute='_compute_amount_all', string='Paid', states={'draft': [('readonly', False)]},
                               readonly=True, digits=0)
    amount_return = fields.Float(compute='_compute_amount_all', string='Returned', digits=0)

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

    @api.depends('statement_ids', 'lines.price_subtotal_incl', 'lines.discount')
    def _compute_amount_all(self):
        for order in self:
            order.amount_paid = order.amount_return = order.amount_tax = 0.0
            currency = order.pricelist_id.currency_id
            order.amount_paid = sum(payment.amount for payment in order.statement_ids)
            order.amount_return = sum(payment.amount < 0 and payment.amount or 0 for payment in order.statement_ids)
            # order.amount_tax = currency.round(sum(self._amount_line_tax(line, order.fiscal_position_id) for line in order.lines))
            amount_untaxed = currency.round(sum(line.price_subtotal for line in order.lines))

            order.brutto_before_tax = currency.round(sum(line.line_brutto_before_tax for line in order.lines))
            order.total_disc_amount_before_tax = currency.round(
                sum(line.line_disc_amount_before_tax for line in order.lines))

            order.amount_untaxed = amount_untaxed
            order.amount_tax = currency.round(sum(line.service_amount + line.tax_amount for line in order.lines))
            order.amount_total = order.amount_tax + order.amount_untaxed
            order.amount_service = currency.round(sum(line.service_amount for line in order.lines))
            order.amount_tax_only = currency.round(sum(line.tax_amount for line in order.lines))

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            # self.pricelist = self.partner_id.property_product_pricelist.id
            self.booking_phone_number = self.partner_id.phone
            self.reserved_by = self.partner_id.name

    @api.model
    def create(self, values):
        booking_number = ""
        if values.get('reservation_pos_id'):
            config_ids = self.env['pos.config'].search([('id', '=', int(values['reservation_pos_id']))], limit=1)
            if config_ids:
                # booking_number = self.get_sequence('POS Reservation','pos.order','B/%s-'%config_ids.name)
                values['name'] = self.get_sequence('POS Reservation', 'pos.order', 'B/%s-' % config_ids.name)
                booking_number = values['name']
        if not booking_number:
            # fallback on any pos.order sequence
            values['name'] = self.env['ir.sequence'].next_by_code('pos.order')

        order = super(KgPosOrderReservation, self).create(values)

        lines = order.lines.mapped('id')
        self.pos_order_updates(order.id, lines)

        return order

    @api.multi
    def write(self, values):
        for rec in self:
            # self.ensure_one()
            if values.get('table_list', None):
                values = rec.check_table_waiting_list(values, values.get('table_list', None))
            else:
                values = rec.check_table_waiting_list(values, rec.table_list)

            if (values.get('reservation_time_start', None) and
                    values.get('reservation_time_start', None) != rec.reservation_time_start) or \
                    (values.get('reservation_time_end', None) and
                     values.get('reservation_time_end', None) != rec.reservation_time_end):
                for t in rec.table_list:
                    rec.recheck_oldest_waiting_list_orders(
                        rec.id, t.table_id.id,
                        rec.reservation_time_start, rec.reservation_time_end)

            res = super(KgPosOrderReservation, self).write(values)
            return res

    @api.model
    def check_table_waiting_list(self, values, table_list):
        if values.get('state_reservation', '') in ('', 'tentative', 'waiting_list',):
            is_waiting = False if self.state_reservation != 'waiting_list' else True
            # if values.get('table_list', None).[0][2].get('is_wating_list', None)
            if values.get('table_list', None):
                for l in table_list:
                    if isinstance(l[2], dict):
                        is_waiting_list = l[2].get('is_waiting_list', None)
                        if is_waiting_list is not None and is_waiting_list:
                            is_waiting = True
                            break
                        elif is_waiting_list is not None:
                            is_waiting = False

            else:
                for l in table_list:
                    if l.is_waiting_list:
                        is_waiting = True
                        break
                    else:
                        is_waiting = False

            if is_waiting:
                values['state_reservation'] = 'waiting_list'
            else:
                values['state_reservation'] = 'tentative'

        return values

    @api.model
    def pos_order_updates(self, order_id, lines):
        # todo: pastikan pos reservation ter-sync ke pos dg baik
        channel_name = "pos_order_sync"
        data = {'order_id': order_id, 'lines': lines}
        self.env['pos.config'].send_to_all_poses(channel_name, data)

    @api.model
    def set_check_in(self, order_id):
        booking_ids = self.sudo().search([('id', '=', order_id)], limit=1)
        if booking_ids:
            booking_ids.write({'state_reservation': 'check_in'})
        return True

    @api.multi
    def set_check_out(self, order_id):
        booking_ids = self.sudo().search([('id', '=', order_id)], limit=1)
        if booking_ids:
            # now = datetime.now()
            now = fields.Datetime.to_string(fields.Datetime.context_timestamp(self, datetime.now()))

            # set checkout if payment time greater than now
            if booking_ids.reservation_time_end and now >= booking_ids.reservation_time_end:
                booking_ids.write({
                    'state_reservation': 'check_out',
                    'state': 'paid',
                })

        return True

    @api.onchange('reservation_time_start')
    def onchange_time_start(self):
        if self.reservation_time_start:
            temp_date = str(self.reservation_time_start)[0:10]
            if datetime.strptime(temp_date, DEFAULT_SERVER_DATE_FORMAT).date() < datetime.now().date():
                warning = {
                    'title': 'Warning',
                    'message': 'Please select a start time equal/or greater than the current date'
                }
                return {'value': {'reservation_time_start': False}, 'warning': warning}

            if self.reservation_time_end:
                for rec in self.table_list:
                    orders = rec.check_existing_order_table(
                        table_id=rec.table_id.id,
                        reservation_time_start=self.reservation_time_start,
                        reservation_time_end=self.reservation_time_end,
                        exclude_reservation_id=self._origin.id if self._origin.id else False
                    )
                    if orders and orders[0].state_reservation == 'check-in':
                        raise UserError("This table is already check-in, choose the different table !")
                    elif orders:
                        value = {'is_waiting_list': True}
                        rec.is_waiting_list = True
                        warning = {
                            'title': 'Warning',
                            'message': 'Order booking already exists in this schedule, you will set to Waiting List !'
                        }
                        return {'value': value, 'warning': warning}
                    else:
                        rec.is_waiting_list = False

    @api.onchange('reservation_time_end')
    def onchange_time_end(self):
        if self.reservation_time_end:
            temp_date = str(self.reservation_time_end)[0:10]
            if datetime.strptime(temp_date, DEFAULT_SERVER_DATE_FORMAT).date() < datetime.now().date():
                warning = {
                    'title': 'Warning',
                    'message': 'Please select an end time equal/or greater than the current date'
                }
                return {'value': {'reservation_time_end': self.reservation_time_start}, 'warning': warning}

            if self.reservation_time_start:
                if self.reservation_time_end < self.reservation_time_start:
                    warning = {
                        'title': 'Warning',
                        'message': 'Please select a end time greater than the start time'
                    }
                    return {'value': {'reservation_time_end': self.reservation_time_start}, 'warning': warning}
                else:
                    for rec in self.table_list:
                        orders = rec.check_existing_order_table(
                            table_id=rec.table_id.id,
                            reservation_time_start=self.reservation_time_start,
                            reservation_time_end=self.reservation_time_end,
                            exclude_reservation_id=self._origin.id if self._origin.id else False
                        )
                        if orders and orders[0].state_reservation == 'check-in':
                            raise UserError("This table is already check-in, choose the different table !")
                        elif orders:
                            value = {'is_waiting_list': True}
                            rec.is_waiting_list = True
                            warning = {
                                'title': 'Warning',
                                'message': 'Order booking already exists in this schedule, '
                                           'you will set to Waiting List !'
                            }
                            return {'value': value, 'warning': warning}
                        else:
                            rec.is_waiting_list = False

    @api.depends('table_list')
    def compute_table_list(self):
        for rec in self:
            table_label = ''
            if rec.table_list:
                for l in rec.table_list:
                    if not table_label:
                        table_label += l.table_id.name
                    else:
                        table_label += ', ' + l.table_id.name

                rec.table_label = table_label

    @api.multi
    def compute_date_order_tz(self):
        for rec in self:
            if rec.date_order:
                user_tz = self.env.user.tz or "UTC"
                local = pytz.timezone(user_tz)
                rec.date_order_tz = datetime.strftime(
                    pytz.utc.localize(datetime.strptime(rec.date_order, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(
                        local), "%Y-%m-%d %H:%M:%S")

    @api.multi
    def compute_time_tz(self):
        for rec in self:
            if rec.reservation_time_start:
                user_tz = self.env.user.tz or "UTC"
                local = pytz.timezone(user_tz)
                if rec.reservation_time_start:
                    rec.reservation_start_date = datetime.strftime(pytz.utc.localize(
                        datetime.strptime(rec.reservation_time_start, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(
                        local), "%Y-%m-%d")

                    rec.start_time_tz = datetime.strftime(pytz.utc.localize(
                        datetime.strptime(rec.reservation_time_start, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(
                        local), "%H:%M:%S")
                if rec.reservation_time_end:
                    rec.end_time_tz = datetime.strftime(pytz.utc.localize(
                        datetime.strptime(rec.reservation_time_end, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),
                                                        "%H:%M:%S")

    def get_sequence(self, name=False, obj=False, pref=False, context=None):
        sequence_id = self.env['ir.sequence'].search([
            ('name', '=', name),
            ('code', '=', obj),
            ('prefix', '=', pref)
        ])
        if not sequence_id:
            sequence_id = self.env['ir.sequence'].sudo().create({
                'name': name,
                'code': obj,
                'implementation': 'no_gap',
                'prefix': pref,
                'padding': 5
            })
        return sequence_id.next_by_id()

    @api.multi
    def action_server_pos_reservation(self):
        res1 = self.env.ref('kg_pos_import_bill.kg_pos_reservation_tree_view')
        res2 = self.env.ref('kg_pos_import_bill.pos_reservation_form_view')
        res3 = self.env.ref('kg_pos_import_bill.kg_pos_order_reservation_search')

        action = {}
        action['name'] = 'Reservation'
        action['type'] = "ir.actions.act_window"
        action['res_model'] = "pos.order,reservation"
        action['view_type'] = "form"
        action['view_mode'] = "tree, form"
        # 'search_view_id': "kg_pos.kg_pos_order_reservation_search",
        action['views'] = [(res1 and res1.id or False, 'tree'),
                           (res2 and res2.id or False, 'form'),
                           (res3 and res3.id or False, 'search')]
        action['context'] = {
            'default_is_reservation': True,
            'default_state_reservation': 'tentative',
            'default_state': 'draft',
            'default_session_id': False,
        }

        action['domain'] = "[('is_reservation','='," + str(True) + ")]"
        return action

    @api.multi
    def btn_kg_definite(self):
        if self.state_reservation == 'waiting_list':
            raise UserError("Waiting list cannot be Definite.")
        else:
            for rec in self.table_list:
                rec.write({'is_waiting_list': False})

            self.write({'state_reservation': 'definite'})

    @api.multi
    def btn_kg_cancel(self):
        ir_model_data = self.env['ir.model.data']
        compose_form_id = ir_model_data.get_object_reference('kg_pos_import_bill', 'wizard_kg_pos_cancel_reservation')[
            1]
        self.cancel_reason = '' if not self.cancel_reason else self.cancel_reason
        return {
            'name': _("Cancel Reservation"),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.kg.pos.cancel.reservation',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': {
                'default_reservation_id': self.id,
                'default_contact_person': self.partner_id.id if self.partner_id else False,

                'default_customer_count': self.customer_count,
                'default_cancel_reason': self.cancel_reason,
            }
        }

    @api.multi
    def action_pos_checkout(self):
        # order_ids = self.env['pos.order'].sudo().search([('reservation_time_end','<=',(datetime.now() +
        # timedelta(hours=-7)).strftime("%Y-%m-%d %H:%M:%S"))])
        # ('state_reservation', 'in', ['check_in', 'waiting_list', 'tentative', 'definite']),
        order_ids = self.env['kg.pos.order.reservation'].sudo().search([
            ('state_reservation', '=', 'check_in'),
            ('reservation_time_end', '<=', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        ])
        if order_ids:
            for rec in order_ids:
                rec.write({'state_reservation': 'check_out'})

    def recheck_oldest_waiting_list_orders(
            self, reservation_id, old_table_id,
            reservation_time_start, reservation_time_end):
        """ Cari semua order dg status yg waiting list, kecuali reservation id ini, utk di check ulang,
        apakah bisa diubah jadi tentative atau tidak

        :param reservation_id:
        :param old_table_id:
        :param reservation_time_start:
        :param reservation_time_end:
        :return:
        """
        orders = self.env['kg.pos.order.reservation'].sudo().search([
            ('table_list.table_id.id', '=', old_table_id),
            ('id', '!=', reservation_id),
            ('state_reservation', '=', 'waiting_list'),
            ('reservation_time_start', '<=', reservation_time_end),
            ('reservation_time_end', '>=', reservation_time_start),
        ], order='id')
        for order in orders:
            is_waiting_list = False
            for table in order.table_list:
                existing_order = table.check_existing_order_table(
                    table_id=table.table_id.id,
                    reservation_time_start=order.reservation_time_start,
                    reservation_time_end=order.reservation_time_end,
                    exclude_reservation_id=reservation_id
                )
                if existing_order:
                    is_waiting_list = True
                    if not table.is_waiting_list:
                        table.is_waiting_list = True
                    break
                else:
                    table.is_waiting_list = False
            if not is_waiting_list:
                order.state_reservation = 'tentative'
                break


class KGPOSOrderTable(models.Model):
    _name = 'kg.pos.order.reservation.table'

    @api.onchange('table_id')
    def onchange_table_list(self):
        if not self.reservation_id.reservation_time_start or not self.reservation_id.reservation_time_end:
            raise UserError("Please set Time Start and Time End first.")

        orders = self.check_existing_order_table(
            table_id=self.table_id.id,
            reservation_time_start=self.reservation_id.reservation_time_start,
            reservation_time_end=self.reservation_id.reservation_time_end,
            exclude_reservation_id=self.reservation_id.id
        )
        if orders and orders[0].state_reservation == 'check-in':
            raise UserError("This table is already check-in, choose the different table !")
        elif orders:
            value = {'is_waiting_list': True}
            warning = {
                'title': 'Warning',
                'message': 'Order booking already exists in this schedule, you will set to Waiting List !'
            }
            return {'value': value, 'warning': warning}
        else:
            return {'value': {'is_waiting_list': False}}

    def check_existing_order_table(
            self, table_id, reservation_time_start, reservation_time_end,
            exclude_reservation_id=False,
            state_reservation=False,
            order_by='state_reservation'):
        if table_id:
            convert_date1 = datetime.strptime(reservation_time_start,
                                              '%Y-%m-%d %H:%M:%S')  # - timedelta(hours=7)
            convert_date1 = convert_date1.strftime("%Y-%m-%d %H:%M:%S")

            convert_date2 = datetime.strptime(reservation_time_end,
                                              '%Y-%m-%d %H:%M:%S')  # - timedelta(hours=7)
            convert_date2 = convert_date2.strftime("%Y-%m-%d %H:%M:%S")

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # TODO: check query tanggal sudah benar tidak utk kasus: jam new = 2 - 5 vs exists definite 3 - 4

            filter_search = [
                ('table_list.table_id.id', '=', table_id),
                ('reservation_time_start', '<=', convert_date2),
                ('reservation_time_end', '>=', convert_date1),
                # '|',
                # '&',
                # ('reservation_id.reservation_time_start', '<=', convert_date1),
                # ('reservation_id.reservation_time_end', '>=', convert_date1),
                # '&',
                # ('reservation_id.reservation_time_start', '<=', convert_date2),
                # ('reservation_id.reservation_time_end', '>=', convert_date2),
            ]

            if not state_reservation:
                state_reservation = ('state_reservation', 'in', ['check_in', 'tentative', 'definite'])
                filter_search.append(state_reservation)
            if exclude_reservation_id:
                filter_search.append(('id', '!=', exclude_reservation_id))

            # CHECK CHECK-IN/tentative/definite
            orders = self.env['kg.pos.order.reservation'].sudo().search(
                filter_search, limit=1, order=order_by)

            if orders:
                return orders
        return False

    reservation_id = fields.Many2one(comodel_name='kg.pos.order.reservation', string='Order ID')
    table_id = fields.Many2one(comodel_name='restaurant.table', string='Table No.', required=True)
    # guest           = fields.Integer('Number of Guest')
    # TODO : remove this function room type if kg banquet done, it's not used here anymore
    functional_room_type = fields.Many2one(comodel_name='function.room.type', string='Function Type', required=False)
    remarks = fields.Char('Remarks', required=False)
    is_waiting_list = fields.Boolean('Waiting List')

    @api.multi
    def write(self, vals):
        for rec in self:
            if vals.get('table_id', None) and vals.get('table_id', None) != rec.table_id.id:
                rec.reservation_id.recheck_oldest_waiting_list_orders(
                    rec.reservation_id.id, rec.table_id.id,
                    rec.reservation_id.reservation_time_start, rec.reservation_id.reservation_time_end)
        super(KGPOSOrderTable, self).write(vals)

    @api.multi
    def unlink(self):
        for rec in self:
            rec.reservation_id.recheck_oldest_waiting_list_orders(
                rec.reservation_id.id, rec.table_id.id,
                rec.reservation_id.reservation_time_start, rec.reservation_id.reservation_time_end)
        super(KGPOSOrderTable, self).unlink()


class KgPosOrderReservationProducts(models.Model):
    _name = 'kg.pos.order.reservation.line'
    # _inherit = "pos.order.line"

    order_id = fields.Many2one('kg.pos.order.reservation', string='Order Ref', ondelete='cascade')

    # <editor-fold desc="Fields from pos order">
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    name = fields.Char(string='Line No', required=True, copy=False)
    notice = fields.Char(string='Discount Notice')
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], required=True, change_default=True)
    price_unit = fields.Float(string='Unit Price', digits=0)
    qty = fields.Float('Quantity', digits=dp.get_precision('Product Unit of Measure'), default=1)
    price_subtotal = fields.Float(compute='_compute_amount_line_all', digits=0, string='Subtotal w/o Tax')
    price_subtotal_incl = fields.Float(compute='_compute_amount_line_all', digits=0, string='Subtotal')
    discount = fields.Float(string='Discount (%)', digits=0, default=0.0)
    create_date = fields.Datetime(string='Creation Date', readonly=True)
    tax_ids = fields.Many2many('account.tax', string='Taxes', readonly=True)
    tax_ids_after_fiscal_position = fields.Many2many('account.tax', compute='_get_tax_ids_after_fiscal_position', string='Taxes')
    pack_lot_ids = fields.One2many('pos.pack.operation.lot', 'pos_order_line_id', string='Lot/serial Number')

    # </editor-fold>

    # <editor-fold desc="custom KG: store subtotals to db">
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
    # </editor-fold>

    @api.depends('price_unit', 'tax_ids', 'qty', 'discount', 'product_id')
    def _compute_amount_line_all(self):
        for line in self:
            fpos = line.order_id.fiscal_position_id
            tax_ids_after_fiscal_position = fpos.map_tax(line.tax_ids, line.product_id,
                                                         line.order_id.partner_id) if fpos else line.tax_ids
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = tax_ids_after_fiscal_position.compute_all(
                price, line.order_id.pricelist_id.currency_id, line.qty,
                product=line.product_id, partner=line.order_id.partner_id)

            # # modification: by aan,
            # 2019-07-11 -- for banquet/pos reservation, no departement expense or office check
            # if line.order_id.employee_id or line.order_id.department_id:
            #     # tax and service not applied for internal transactions
            #     amount_with_tax = taxes['total_excluded']
            #     service_amount = 0
            # else:
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
            })

    def create(self, values):
        if not values.get('name'):
            time_now = datetime.now()
            values['name'] = '{date_now}-{unique_char1}{unique_char2}'.format(
                date_now=time_now.strftime('%y%m%d-%H%M%S-.%f'),
                unique_char1=random.choice(string.ascii_lowercase),
                unique_char2=random.choice(string.ascii_lowercase)
            )

        return super(KgPosOrderReservationProducts, self).create(values)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            if not self.order_id.pricelist_id:
                raise UserError(
                    _('You have to select a pricelist in the sale form !\n'
                      'Please set one before choosing a product.'))
            price = self.order_id.pricelist_id.get_product_price(
                self.product_id, self.qty or 1.0, self.order_id.partner_id)
            self._onchange_qty()
            self.tax_ids = self.product_id.taxes_id.filtered(lambda r: not self.company_id or r.company_id == self.company_id)
            fpos = self.order_id.fiscal_position_id
            tax_ids_after_fiscal_position = fpos.map_tax(self.tax_ids, self.product_id, self.order_id.partner_id) if fpos else self.tax_ids
            self.price_unit = self.env['account.tax']._fix_tax_included_price_company(price, self.product_id.taxes_id, tax_ids_after_fiscal_position, self.company_id)

    @api.onchange('qty', 'discount', 'price_unit', 'tax_ids')
    def _onchange_qty(self):
        if self.product_id:
            if not self.order_id.pricelist_id:
                raise UserError(_('You have to select a pricelist in the sale form !'))
            price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
            self.price_subtotal = self.price_subtotal_incl = price * self.qty
            if (self.product_id.taxes_id):
                taxes = self.product_id.taxes_id.compute_all(price, self.order_id.pricelist_id.currency_id, self.qty, product=self.product_id, partner=False)
                self.price_subtotal = taxes['total_excluded']
                self.price_subtotal_incl = taxes['total_included']

    @api.multi
    def _get_tax_ids_after_fiscal_position(self):
        for line in self:
            line.tax_ids_after_fiscal_position = line.order_id.fiscal_position_id.map_tax(line.tax_ids, line.product_id, line.order_id.partner_id)


class RestaurantTable(models.Model):
    _inherit = 'restaurant.table'

    current_booking = fields.Integer(string='Today Booking', compute='_compute_current_booking')

    @api.multi
    def _compute_current_booking(self):
        for rec in self:
            booking_ids = self.env['kg.pos.order.reservation.table'].search([
                ('table_id.id', '=', rec.id),
                ('reservation_id.state_reservation', 'in', ['definite', 'check_in']),
                # ('reservation_id.state_reservation', '=', 'definite'),
                ('reservation_id.is_reservation', '=', True),
                ('reservation_id.reservation_time_start', '<=', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                ('reservation_id.reservation_time_end', '>=', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ])
            rec.current_booking = len(booking_ids)
