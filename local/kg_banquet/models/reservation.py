from datetime import datetime
from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError


class KGBanquetReservation(models.Model):
    _name = 'banquet.reservation'
    _inherit = ['mail.thread']
    _description = "Banquet Reservation"

    name = fields.Char()
    partner_id = fields.Many2one(
        string='Customer',
        comodel_name='res.partner',
        domain="[('is_company', '=', True)]",
        track_visibility='onchange'
    )
    deposit_ids = fields.One2many('account.payment', 'bqt_reservation_id', ondelete='set null')
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.user.company_id.id)
    contact_id = fields.Many2one(comodel_name='res.partner', string="Contact Person",
                                 domain="[('type', 'in', ['contact']),"
                                        "('parent_id','=',partner_id)]",
                                 track_visibility='onchange')
    sales_id = fields.Many2one(comodel_name='hr.employee', string='Salesperson', track_visibility='onchange',
                               domain="[('is_salesperson', '=', True)]")
    proposal_id = fields.Many2one(
        comodel_name='banquet.proposal', string="Proposal", track_visibility='onchange'
        , clone=False
        , ondelete='set null')
    contract_no = fields.Char(related='proposal_id.contract_no', string="Contract", clone=False)
    reservation_by = fields.Char(track_visibility='onchange')
    phone_no = fields.Char(string="Booker Contact")
    working_date = fields.Date(default=fields.Date.context_today)
    description = fields.Char()
    state = fields.Selection([
        ('new', ''),
        ('draft', 'Draft'),
        ('proposal', 'Proposal'),
        ('contract', 'Contract'),
        ('signed', 'Signed'),
        ('approved', 'Approved'),
        ('beo', 'BEO'),
        ('checkin', 'Check In'),
        ('checkout', 'Check Out'),
        ('release', 'Released')
    ], string='Flow Status', track_visibility='onchange'
        , store=True, default='new')
    banquet_status = fields.Selection([
        ('waiting', 'WAITING LIST'),
        ('tentative', 'TENTATIVE'),
        ('definite', 'DEFINITE')
    ], default='tentative', readonly="True", track_visibility='onchange')
    payment_state = fields.Selection([
        ('actual', 'ACTUAL'),
        ('late', 'LATE')
    ], default='actual', readonly="True", track_visibility='onchange')

    reservation_date = fields.Date(track_visibility='onchange', default=fields.Date.today())
    cut_off_date = fields.Date(required=True)
    remark = fields.Text(track_visibility='onchange')
    internal_note = fields.Text(track_visibility='onchange')
    event_type_id = fields.Many2one('catalog.eventtype', 'Event Type', required=True, track_visibility='onchange')
    payment_journal_id = fields.Selection([
        ('cash', 'CASH'),
        ('credit_card', 'CREDIT CARD'),
        ('city_ledger', 'CITY LEDGER'),
        ('transfer', 'TRANSFER')
    ],  'Payment Type',  track_visibility='onchange')
    cancel_reason = fields.Text(readonly=True, track_visibility='onchange')
    is_release = fields.Boolean(readonly=True)
    is_from_crm = fields.Boolean(readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id)
    reservation_event_ids = fields.One2many('banquet.reservation.event', 'reservation_id', track_visibility='onchange')
    reservation_rate_ids = fields.One2many('banquet.reservation.rate', 'reservation_id', track_visibility='onchange')
    reservation_resident_ids = fields.One2many('banquet.reservation.resident', 'reservation_id', track_visibility='onchange')

    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position', string='Fiscal Position',
        readonly=True
    )
    reservation_folio_ids = fields.One2many('banquet.reservation.folio', 'reservation_id')

    last_amendment_no = fields.Integer(
        'Last Amendment No',
        default=0,
        track_visibility='always'
    )
    old_amendment_no = fields.Integer(default=0)
    is_in_amendment = fields.Boolean(default=False, track_visibility='onchange')

    total_attendance = fields.Integer(string='Total Attendance', compute='sum_rate_attendance', store=False)
    arrival_date = fields.Date(string='Arrival Date', compute='get_first_last_event', store=False)
    departure_date = fields.Date(string='Departure Date', compute='get_first_last_event', store=False)

    @api.depends('reservation_rate_ids')
    def sum_rate_attendance(self):
        for rec in self:
            if rec.reservation_rate_ids:
                rec.total_attendance = sum(attd.attendance for attd in rec.reservation_rate_ids)
            else:
                rec.total_attendance = 0

    @api.depends('reservation_event_ids')
    def get_first_last_event(self):
        for rec in self:
            if rec.reservation_event_ids:
                # first_event_date = self.env['banquet.reservation.event'].search([('reservation_id', '=', rec.id)], order='date asc')[0].date
                # last_event_date = self.env['banquet.reservation.event'].search([('reservation_id', '=', rec.id)], order='date desc')[0].date
                rec.arrival_date = min(arrival.date for arrival in rec.reservation_event_ids)
                rec.departure_date = max(departure.date for departure in rec.reservation_event_ids)

    @api.multi
    def activate_amendment(self):
        self.ensure_one()
        self.old_amendment_no = self.last_amendment_no
        self.last_amendment_no += 1
        self.is_in_amendment = True
        if self.reservation_event_ids:
            for event in self.reservation_event_ids:
                event.activate_amendment()
        # if self.state == 'signed':
        #     if not self.reservation_event_ids:
        #         raise UserError('Please add reservation events first')
        #     else:
        #         self.banquet_status = 'definite'
        # else:
        #     raise UserError('Please check banquet flow status')

    @api.multi
    def deactivate_amendment(self):
        self.ensure_one()
        self.is_in_amendment = False

    @api.multi
    def button_definite(self):
        self.ensure_one()
        if self.state == 'signed':
            if not self.reservation_event_ids:
                raise UserError('Please add reservation events first')
            else:
                self.banquet_status = 'definite'
        else:
            raise UserError('Please check banquet flow status')

    @api.multi
    def button_approve(self):
        self.ensure_one()
        if self.state == 'signed' and self.banquet_status == 'definite':
            self.state = 'approved'
        else:
            raise UserError('Please check banquet flow status')

    @api.multi
    def button_beo(self):
        self.ensure_one()
        if self.state == 'approved' and self.banquet_status == 'definite':
            self.state = 'beo'
        else:
            raise UserError('Please check banquet flow status')

    @api.multi
    def button_checkin(self):
        self.ensure_one()
        start_date = str(
            self.env['banquet.reservation.event'].search([('reservation_id', '=', self.id)], order='date asc')[0].date)
        # start_date = str(self.reservation_event_ids.search([('reservation_id', '=', self.id)], order='date asc')[0].date)
        today_date = str(datetime.now().date())
        if self.state == 'beo' and self.banquet_status == 'definite':
            if start_date == today_date:
                self.state = 'checkin'
            elif start_date > today_date:
                raise UserError('Too soon for check in.')
            else:
                raise UserError('Too late for check in.')
        else:
            raise UserError('Please check banquet flow status.')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('banquet.reservation.name')
        res = super(KGBanquetReservation, self).create(vals)
        if res.state == 'new':
            res.state = 'draft'
        return res

    @api.multi
    def write(self, vals):
        res = super(KGBanquetReservation, self).write(vals)
        # if self.state == 'new':
        #     self.state = 'draft'
        return res

    @api.multi
    def copy(self, default=None):
        default = dict(default or {})
        self.ensure_one()
        default.update({
            'state': 'new',
            'proposal_id': None,
            'cut_off_date': fields.Date.today(),
            'reservation_date': fields.Date.today(),
            'last_amendment_no': 0,
            'is_in_amendment': False
        })
        return super(KGBanquetReservation, self).copy(default)

    @api.onchange('partner_id')
    def _onchange_contact_customer(self):
        if self.partner_id:
            self.contact_id = self.partner_id
            self.phone_no = None
            self.contact_id = None

    @api.onchange('contact_id')
    def _onchange_contact_person(self):
        if self.contact_id is None:
            self.phone_no = None
        else:
            self.phone_no = self.contact_id.phone

    @api.multi
    def reservation_checkout(self):
        self.ensure_one()
        last_event_date = str(
            self.env['banquet.reservation.event'].search([('reservation_id', '=', self.id)], order='date desc')[0].date)
        # str(self.reservation_event_ids.search([], order='date desc')[0].date)
        today_date = str(datetime.now().date())
        # last_folio_date = str(self.reservation_folio_ids.search([], order='date desc')[0].date)
        # balance = str(self.reservation_folio_ids.total_amount - self.reservation_folio_ids.paid_amount)
        # amount_folio = str(self.reservation_folio_ids.total_amount)
        current_adm = self.env['ir.module.category'].search([('name', '=', 'Administration')])

        for checkout in self:
            current_session_checkout = self.search(
                [('state', '=', 'checkin'),
                 ('banquet_status', '=', 'definite')], limit=1)
            # TODO add condition balance = 0 and --> TBC
            #  condition last folio date >= date of the last event --> TBC

            if not current_session_checkout:
                raise UserError(
                    _('Please check banquet flow status'))

            if today_date < last_event_date:
                raise UserError('Event is still running, banquet reservation cannot be checked out')

            if today_date == last_event_date:
                self.write({'payment_state': 'actual'})

            if today_date > last_event_date:
                if current_adm:
                    self.write({'payment_state': 'late'})
                else:
                    raise UserError('Banquet reservation cant be check out, User group not match')

            if checkout.is_in_amendment:
                self.write({'is_in_amendment': False})

        return self.write({'state': 'checkout'})

    @api.multi
    def reservation_release(self):
        self.ensure_one()
        for rec in self:
            check_deposit = rec.deposit_ids.bqt_reservation_id
            if rec.id == check_deposit:
                raise UserError('Please check deposit')
            if rec.is_in_amendment:
                self.write({'is_in_amendment': False})

        ir_model_data = self.env['ir.model.data']
        compose_form_id = ir_model_data.get_object_reference('kg_banquet', 'wizard_cancel_reason_banquet_reservation')[1]
        self.cancel_reason = '' if not self.cancel_reason else self.cancel_reason
        return {
            'name': _("Release Reservation "),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.cancel.reason.banquet.reservation',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': {
                'default_reservation_id': self.id,
                'default_is_release': self.is_release,
                'default_cancel_reason': self.cancel_reason,
            }
        }

    @api.multi
    def action_auto_checkin(self):
        today_date = str(datetime.now().date())
        reservation_ids = self.env['banquet.reservation'].sudo().search([
            ('state', '=', 'beo'),
            ('banquet_status', '=', 'definite'),
        ])
        if reservation_ids:
            for reservation in reservation_ids:
                first_event_date = str(self.env['banquet.reservation.event'].search([('reservation_id', '=', reservation.id)], order='date asc')[0].date)
                if first_event_date == today_date:
                    reservation.write({'state': 'checkin'})

    @api.multi
    def action_auto_checkout(self):
        today_date = str(datetime.now().date())
        reservation_ids = self.env['banquet.reservation'].sudo().search([
            ('state', '=', 'checkin'),
        ])
        if reservation_ids:
            for reservation in reservation_ids:
                last_event_date = str(self.env['banquet.reservation.event'].search([('reservation_id', '=', reservation.id)], order='date desc')[0].date)
                if last_event_date <= today_date:
                    # TODO add condition balance = 0 and last_folio_date >= last_event_date
                    reservation.write({'state': 'checkout'})
                    reservation.write({'cancel_reason': 'AUTOMATICALLY CHECK OUT BY SYSTEM'})

    @api.multi
    def action_auto_release(self):
        today_date = str(datetime.now().date())
        reservation_ids = self.env['banquet.reservation'].sudo().search([
            ('state', 'in', ['draft', 'proposal', 'contract']),
            ('cut_off_date', '<', today_date),
        ])
        if reservation_ids:
            for reservation in reservation_ids:
                reservation.write({'state': 'release'})
                reservation.write({'cancel_reason': 'AUTOMATICALLY RELEASED BY SYSTEM'})

    @api.onchange('partner_id', 'payment_journal_id')
    def payment_type_check(self):
        if self.partner_id:
            if self.payment_journal_id == 'city_ledger' and self.partner_id.allow_use_city_ledger is False:
                self.payment_journal_id = None
                warning = {
                    'title': 'Warning',
                    'message': 'Payment Type City Ledger is not allowed for this company'
                }
                return {'value': {'payment_journal_id': False}, 'warning': warning}

    @api.onchange('reservation_date', 'cut_off_date')
    def check_date(self):
        if self.reservation_date and self.cut_off_date:
            if datetime.strptime(self.cut_off_date, '%Y-%m-%d').date() < datetime.strptime(self.reservation_date, '%Y-%m-%d').date():
                self.cut_off_date = self.reservation_date
                raise UserError("You can't select cut off date earlier than reservation date")
