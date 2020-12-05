from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class ReservationResident(models.Model):
    _name = 'banquet.reservation.resident'
    _inherit = ['mail.thread']
    _description = "Reservation Residential"

    # guest_name = fields.Selection(selection='_get_guest_profile', string='Guest Name')
    reservation_id = fields.Many2one('banquet.reservation', string='Reservation')
    pms_reservation_no = fields.Char()
    reservation_by = fields.Char("Reservation By")
    partner_id = fields.Many2one('res.partner', string="Company")
    room_type_id = fields.Many2one('banquet.room.type')
    rate_type_id = fields.Many2one('banquet.rate.type')

    person = fields.Selection(selection=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'),
                                         (6, '6'), (7, '7'), (8, '8'), (9, '9'), (10, '10')])
    company_id = fields.Many2one('res.company', related='reservation_id.company_id')
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True,
                                          help='Utility field to express amount currency')
    # base_amount = fields.Many2one('amount.pms')
    base_amount = fields.Monetary(string='Base Amount', default=0, currency_field='company_currency_id')

    market_segment_id = fields.Many2one('banquet.market.segment')
    reservation_source_id = fields.Many2one('banquet.reservation.source')
    arrival_date = fields.Date("Date Arrive")
    departure_date = fields.Date("Date Departure")
    pax = fields.Integer("Pax")
    extra_bed = fields.Integer("Extra Bed")

    remark = fields.Char("Remark")
    reservation_pms_id = fields.Integer("Group Id")
    phone_number = fields.Char("Phone Number")
    status_pms = fields.Integer()
    status_amd = fields.Integer()
    total_nights = fields.Integer(string="Nights")
    copies_value = fields.Integer(string="Copies")
    state_reservation = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancel')
    ], string='State Reservation', track_visibility='onchange', default='draft')

    @api.model
    def _get_default_number(self):
        return self.env['ir.sequence'].next_by_code('banquet.reservation.residential.number')

    name = fields.Char(string='Number', required=True,
                       default=_get_default_number,
                       track_visibility='onchange')

    @api.onchange('arrival_date')
    def calculate_arrival_date(self):
        if self.arrival_date:
            if datetime.strptime(self.arrival_date, '%Y-%m-%d').date() < datetime.now().date():
                self.arrival_date = ''
                raise UserError("You can't select date earlier than today")
            else:
                self.departure_date = ''

    @api.onchange('departure_date', 'total_nights')
    def calculate_date(self):
        if self.arrival_date and self.departure_date:
            if datetime.strptime(self.departure_date, '%Y-%m-%d').date() < \
                    datetime.strptime(self.arrival_date, '%Y-%m-%d').date():
                self.departure_date = None
                self.total_nights = None
                raise UserError("You can't select departure date earlier than arrival date")
            else:
                d1 = datetime.strptime(str(self.arrival_date), '%Y-%m-%d')
                d2 = datetime.strptime(str(self.departure_date), '%Y-%m-%d')
                d3 = d2 - d1
                self.total_nights = str(d3.days)

    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        for rec in self:
            for i in range(rec.copies_value):
                default = dict(default or {})
                default.update({
                    'name': rec.env['ir.sequence'].next_by_code('banquet.reservation.residential.number'),
                })
                rec = super(ReservationResident, rec).copy(default)
                if i == 0:
                    rec.copies_value = 0
            return rec

    @api.multi
    def action_cancel(self):
        for reservation in self:
            if reservation.state_reservation == 'draft':
                reservation.state_reservation = 'cancel'
            else:
                raise UserError('You cannot cancel a reservation residential which is not in draft state.')

    @api.onchange('guest_info')
    def _change_guest_info(self):
        for rec in self:
            if rec.guest_info and '--' in rec.guest_info:
                guest_pms_id = int(rec.guest_info.split('--')[0].strip())
                guest_name = rec.guest_info.split('--')[1].strip()
            else:
                guest_pms_id = False
                guest_name = ""
            rec.update({
                'guest_pms_id': guest_pms_id,
                'guest_name': guest_name,
            })

    guest_pms_id = fields.Integer(compute=_change_guest_info, store=True, readonly=False)
    guest_name = fields.Char(compute=_change_guest_info, store=True, readonly=False)

    guest_info = fields.Char(store=False, readonly=False)

    @api.onchange('group_info')
    def _change_group_info(self):
        for rec in self:
            if rec.group_info and '--' in rec.group_info:
                group_id = int(rec.group_info.split('--')[0].strip())
                group_name = rec.group_info.split('--')[1].strip()
            else:
                group_id = 0
                group_name = False
            rec.update({
                'group_id': group_id,
                'group_name': group_name
            })
    group_id = fields.Integer(compute=_change_group_info, store=True, readonly=False)
    group_name = fields.Char(compute=_change_group_info, store=True, readonly=False)

    group_info = fields.Char(store=False, readonly=False)

    @api.onchange('room_rate_info')
    def _change_room_rate_info(self):
        for rec in self:
            if rec.room_rate_info and '--' in rec.room_rate_info:
                room_rate_id = rec.room_rate_info.split('--')[0].strip()
                amount = int(rec.room_rate_info.split('--')[1].strip())
                extra_bed_charge = int(rec.room_rate_info.split('--')[2].strip())
            else:
                amount = 0
                room_rate_id = False
                extra_bed_charge = 0
            rec.update({
                'amount': amount,
                'room_rate_id': room_rate_id,
                'extra_bed_charge': extra_bed_charge
            })

    room_rate_id = fields.Char(compute=_change_room_rate_info, store=True, readonly=False)
    amount = fields.Integer(compute=_change_room_rate_info, store=True, readonly=False)
    extra_bed_charge = fields.Integer(compute=_change_room_rate_info, store=True, readonly=False)

    room_rate_info = fields.Char(store=False, readonly=False)

    @api.model
    def search_guest_pms(self, *args, **kwargs):
        name = kwargs.get('name')
        email = kwargs.get('email')
        phone = kwargs.get('phone')
        response = self.env['banquet.helpers'].get_guest_info(name=name, email=email, phone=phone)
        if response:
            lst = []
            for r in response:
                if name.upper() in r['GuestName'].upper() or email.upper() in r['EmailAddress'] \
                        or phone.upper() in r['MobilePhone']:
                    lst.append(r)
        else:
            raise UserWarning('Empty List')
        return lst

    @api.model
    def search_group_pms(self, *args, **kwargs):
        response = self.env['banquet.helpers'].get_group_info()
        search = kwargs.get('search')
        if response:
            lst = []
            for r in response:
                if search.upper() in r['GroupDescription'].upper():
                    lst.append(r)
        else:
            raise UserWarning('Empty List')
        return lst

    @api.model
    def search_room_rate_pms(self, *args, **kwargs):
        rate_type = kwargs.get('rate_type')
        room_type = kwargs.get('room_type')
        arrival_date = kwargs.get('arrival_date')
        person = kwargs.get('person')
        search = kwargs.get('search')
        if rate_type and room_type and arrival_date and person:
            rate = str(self.env['banquet.rate.type'].search([('id', '=', rate_type)])[0].pms_id)
            room = str(self.env['banquet.room.type'].search([('id', '=', room_type)])[0].pms_id)
            response = self.env['banquet.helpers'].get_room_rate_info(rate_type=rate, room_type=room
                                                                      , person=person, arrival_date=arrival_date)
        else:
            raise UserWarning('Please fill field properly')
        if response:
            lst = []
            for r in response:
                if search.upper() in r['RateType']:
                    lst.append(r)
        else:
            raise UserWarning('Empty List')
        return lst

    # @api.model
    # def create(self, vals):
    #     num = 0
    #     num = 0 +self.copies_value
    #     for i in range(num):
    #         vals = dict(vals or {})
    #         vals.update({
    #             'name': self.env['ir.sequence'].next_by_code('banquet.reservation.residential.number'),
    #         })
    #     rec = super(ReservationResident, self).create(vals)
    #     return rec

    # def _get_guest_profile(self):
    #
    #     response = self.env['pos.helpers'].get_pms_guest_profile()
    #     lst = []
    #     if response:
    #         for r in response:
    #             lst.append((r['GuestId'], r['GuestName']))
    #     return lst

