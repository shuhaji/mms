from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError
import pytz


class ReservationEvent(models.Model):
    _name = 'banquet.reservation.event'
    _inherit = ['mail.thread']
    _description = "Reservation Event"

    name = fields.Char(readonly=True, copy=False)

    reservation_id = fields.Many2one('banquet.reservation',
                                     'Reservation', track_visibility='onchange',
                                     domain=[('state', 'not in', ('checkout', 'release'))])
    company_id = fields.Many2one(comodel_name='res.company', string='Company',
                                 required=True, default=lambda self: self.env.user.company_id.id,
                                 track_visibility='onchange')
    partner_id = fields.Many2one(
        string='Customer',
        comodel_name='res.partner',
        related='reservation_id.partner_id',
        store=False
    )
    function_room_id = fields.Many2one('banquet.function.room',
                                       'Function Room', track_visibility='onchange', required=True)
    function_room_setup_id = fields.Many2one('banquet.function.room.setup',
                                             'Func.Room Setup', track_visibility='onchange', required=True)
    # package_id = fields.Many2one('banquet.package',
    #                              'Package', track_visibility='onchange')
    event_function_id = fields.Many2one('banquet.event.function',
                                        'Event Function', track_visibility='onchange', required=True)
    parent_id = fields.Many2one('banquet.reservation.event', 'Main Event',
                                domain=[('parent_id', '=', False), ('reservation_state', 'not in', ('checkout', 'release'))],
                                track_visibility='onchange')
    children_ids = fields.One2many('banquet.reservation.event', 'parent_id', 'Sub Events')

    resources_ids = fields.One2many('banquet.reservation.event.resources', 'reservation_event_id')
    additional_ids = fields.One2many('banquet.reservation.event.additional.resources', 'reservation_event_id')
    instruction_ids = fields.One2many('banquet.reservation.event.instruction', 'reservation_event_id')

    date = fields.Date(string='Date', track_visibility='onchange', required=True, default=fields.Date.context_today)
    start_time = fields.Char(string='Start Time', track_visibility='onchange', required=True, default='00:00')
    date_start = fields.Datetime(compute='_compute_date_start_end', store=True)
    end_time = fields.Char(string='End Time', track_visibility='onchange', required=True, default='00:00')
    date_end = fields.Datetime(compute='_compute_date_start_end', store=True)

    setup_time = fields.Integer(string='Setup Time', required=True)
    setdown_time = fields.Integer(string='Setdown Time', required=True)
    price_event = fields.Monetary(string='Price Event Function')
    meter_occupied = fields.Integer(string='Meter Occupied')
    meter_charge = fields.Integer(string='Meter Charge')
    function_room_amount = fields.Monetary(string='Function Room Charge', track_visibility='onchange')
    currency_id = fields.Many2one(related='reservation_id.currency_id')
    location = fields.Char(track_visibility='onchange')
    attendees = fields.Integer(track_visibility='onchange', required=True)
    print_count_amd = fields.Integer(string='Print Count Amendment', track_visibility='onchange')
    # blocking_state = fields.Boolean(string='Blocking State')
    # posting_state = fields.Boolean(string='Posting State')
    waiting_list = fields.Integer(string='Waiting List')
    remark = fields.Char(track_visibility='onchange')
    beo_issued = fields.Boolean(string='BEO', readonly=True)
    use_meter = fields.Boolean(string='Use Meter Charge', track_visibility='onchange')

    # amendment information -- start
    # amd_state = fields.Char(string='Amendment State', track_visibility='onchange')
    is_in_amendment = fields.Boolean(related='reservation_id.is_in_amendment')
    reservation_state = fields.Selection([
        ('draft', 'Draft'),
        ('proposal', 'Proposal'),
        ('contract', 'Contract'),
        ('signed', 'Signed'),
        ('approved', 'Approved'),
        ('beo', 'BEO'),
        ('checkin', 'Check In'),
        ('checkout', 'Check Out'),
        ('release', 'Released')], related='reservation_id.state')
    # we need to store amendment no here also, for filtering purpose in reports
    amendment_no = fields.Integer(string="Amendment No", default=0, track_visibility='always')
    pivot_amd_no = fields.Integer(string="Pivot Amendment No", default=0, track_visibility='onchange')
    old_start_time = fields.Char(track_visibility='onchange', default=0.00)
    old_end_time = fields.Char(track_visibility='onchange', default=0.00)
    old_function_room_id = fields.Many2one(
        'banquet.function.room', 'Old Function Room', track_visibility='onchange')
    old_function_room_setup_id = fields.Many2one(
        'banquet.function.room.setup', 'Old F.Room Setup', track_visibility='onchange')
    old_attendees = fields.Integer(track_visibility='onchange')
    # amendment information -- end

    def _default_hotel_convention(self):
        return self.env.user.company_id.hotel_convention
    hotel_convention = fields.Boolean(default=_default_hotel_convention)

    # default=lambda self: getattr(self.env.user.company_id, 'hotel_convention') if
    #     hasattr(self.env.user.company_id, 'hotel_convention') else False)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('banquet.reservation.event.name')
        # default values for amendment_no was set in xml , search default_amendment_no in context
        # vals['pivot_amd_no'] = vals.get('amendment_no',
        #                                 self.reservation_id.last_amendment_no if self.reservation_id else 0)
        res = super(ReservationEvent, self).create(vals)
        return res

    # @api.depends('reservation_id', 'amendment_no', 'start_time',
    #              'end_time', 'function_room_id', 'function_room_setup_id', 'attendees')
    # def _set_old_values_amendment(self):
    #     if

    @api.multi
    def write(self, values):
        if self.is_in_amendment:
            pivot_amd_no = values.get('pivot_amd_no', self.pivot_amd_no)
            amendment_no = values.get('amendment_no', self.amendment_no)
            if pivot_amd_no != amendment_no and (
                (values.get('start_time') and values.get('start_time', '') != self.old_start_time)
                or (values.get('end_time') and values.get('end_time', '') != self.old_end_time)
                or (values.get('function_room_id') and
                    values.get('function_room_id', False) != self.old_function_room_id.id)
                or (values.get('function_room_setup_id') and
                    values.get('function_room_setup_id', False) != self.old_function_room_setup_id.id)
                or (values.get('attendees') and values.get('old_attendees', 0) != self.old_attendees)
            ):
                # update old values
                values['pivot_amd_no'] = amendment_no
                values['old_start_time'] = self.start_time
                values['old_end_time'] = self.end_time
                values['old_function_room_id'] = self.function_room_id.id
                values['old_function_room_setup_id'] = self.function_room_setup_id.id
                values['old_attendees'] = self.attendees

        res = super(ReservationEvent, self).write(values)
        return res

    @api.onchange('reservation_id')
    def onchange_reservation_id(self):
        if not self._origin.reservation_id and self.reservation_id:
            self.amendment_no = self.reservation_id.last_amendment_no

    def button_activate_amendment(self):
        # activate amendment via Reservation (all events should be in amendment)
        self.reservation_id.activate_amendment()

    @api.multi
    def activate_amendment(self):
        self.ensure_one()
        self.pivot_amd_no = self.get_old_amendment_no()
        self.amendment_no = self.get_amendment_no()
        for resource in self.resources_ids:
            resource.amendment_no = self.amendment_no
        for add_resource in self.additional_ids:
            add_resource.amendment_no = self.amendment_no
        for instruction in self.instruction_ids:
            instruction.amendment_no = self.amendment_no

    def get_amendment_no(self):
        return self.reservation_id.last_amendment_no if self.reservation_id else 0

    def get_old_amendment_no(self):
        return self.reservation_id.old_amendment_no if self.reservation_id else 0

    @api.onchange('function_room_id')
    def _default_func_amount(self):
        self.function_room_amount = self.function_room_id.price_total
        self.function_room_setup_id = None

    @api.onchange('use_meter')
    def _default_use_meter(self):
        if self.use_meter is True:
            self.meter_occupied = self.function_room_id.area
            self.meter_charge = self.function_room_id.price_per_meter
            self.function_room_amount = self.function_room_id.area * self.function_room_id.price_per_meter
        else:
            self.meter_occupied = 0
            self.meter_charge = 0
            self.function_room_amount = self.function_room_id.price_total

    @api.onchange('function_room_setup_id')
    def _default_setup_setdown_time(self):
        self.setdown_time = self.function_room_setup_id.setdown_time
        self.setup_time = self.function_room_setup_id.setup_time

    @api.onchange('date')
    def onchange_date(self):
        if self.date:
            if datetime.strptime(self.date, '%Y-%m-%d').date() < datetime.now().date():
                warning = {
                    "title": "Warning",
                    "message": "You can't select date earlier than today"
                }
                return {'value': {'date': fields.Date.context_today()}, 'warning': warning}

    @api.depends('date', 'start_time', 'end_time')
    def _compute_date_start_end(self):
        user_tz = self.env.user.tz or "UTC"
        local = pytz.timezone(user_tz)
        utc_tz = pytz.timezone("UTC")
        for event in self:
            start = "{date} {time}:00".format(date=event.date, time=event.start_time)
            date_start_local = fields.Datetime.from_string(start)
            date_start_local_tz = local.localize(date_start_local)
            end = "{date} {time}:00".format(date=event.date, time=event.end_time)
            end_tz = local.localize(fields.Datetime.from_string(end))
            event.update({
                "date_start": date_start_local_tz.astimezone(utc_tz),  # must be stored in db as UTC Timezone
                "date_end": end_tz.astimezone(utc_tz)
            })

    @api.onchange('start_time')
    def check_start_time(self):
        if self.start_time:
            if datetime.strptime(self.start_time, '%H:%M') > datetime.strptime(self.end_time, '%H:%M'):
                self.end_time = self.start_time

    @api.onchange('end_time')
    def check_end_time(self):
        if self.end_time:
            if datetime.strptime(self.start_time, '%H:%M') > datetime.strptime(self.end_time, '%H:%M'):
                self.end_time = self.start_time
                warning = {
                    "title": "Warning",
                    "message": "You can't select Start Time greater than End Time"
                }
                return {'warning': warning}

