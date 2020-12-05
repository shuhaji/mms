from datetime import timedelta
from dateutil import parser
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class KgAccountPeriod(models.Model):
    _name = 'account.period'
    _order = 'id desc'

    name = fields.Char()

    # TODO: Create index multi field
    company_id = fields.Many2one(
        'res.company', string='Company', change_default=True,
        required=True, readonly=True,
        default=lambda self: self.env.user.company_id)

    def _default_date_start(self):
        date_val = parser.parse(fields.Date.context_today(self))
        return date_val.replace(day=1)

    period = fields.Date(default=_default_date_start)
    period_info = fields.Char(compute='_compute_period', store=False, string="Period")
    date_start = fields.Date()
    date_end = fields.Date()

    _sql_constraints = [
        ('account_period_unique', 'unique(company_id,date_start,date_end)',
         "Period for this company already exists!"),
    ]

    @api.onchange('period')
    def period_onchange(self):
        for rec in self:
            rec.name = "{company}:{period}".format(
                company=rec.company_id.id, period=rec.period[:7])
            date_val = parser.parse(rec.period) if rec.period else False
            if date_val:
                date_start = date_val.replace(day=1)
                rec.date_start = date_start
                rec.date_end = date_start.replace(month=date_start.month + 1) - timedelta(days=1)

    @api.depends('period')
    def _compute_period(self):
        for rec in self:
            rec.period_info = rec.period[:7] if rec.period else ""

    close_all = fields.Boolean(store=False)
    is_gl_closed = fields.Boolean(
        string="GL Closed",
        )
    is_ar_closed = fields.Boolean(
        string="AR Closed",
        )
    is_pos_closed = fields.Boolean(
        string="POS Closed",
        )
    is_ap_closed = fields.Boolean(
        string="AP/Internal Transfer Closed",
        )
    is_bank_statement_closed = fields.Boolean(
        string="Bank Statement Closed",
        )

    @api.onchange('close_all')
    def close_all_onchange(self):
        if self.close_all:
            self.is_ap_closed = True
            self.is_ar_closed = True
            self.is_gl_closed = True
            self.is_pos_closed = True
            self.is_bank_statement_closed = True

    @staticmethod
    def check_lock_period_account_move(resource, move):
        lock_period, message = KgAccountPeriod.get_period(resource, move.company_id.id, move.date)
        if lock_period:
            for move_line in move.line_ids:
                if move_line.invoice_id:
                    if move_line.invoice_id.type in ['out_invoice', 'out_refund']:
                        if lock_period.is_ar_closed:
                            raise UserError(message.format(type="AR"))
                    else:
                        if lock_period.is_ap_closed:
                            raise UserError(message.format(type="AP"))
                elif move_line.payment_id:
                    if move_line.payment_id.partner_type == 'customer':
                        if lock_period.is_ar_closed:
                            raise UserError(message.format(type="AR"))
                    else:
                        if lock_period.is_ap_closed:
                            raise UserError(message.format(type="AP/Internal Transfer"))
                elif move_line.statement_id:
                    if lock_period.is_bank_statement_closed:
                        raise UserError(message.format(type="Bank Statement"))
                else:
                    if lock_period.is_gl_closed:
                        raise UserError(message.format(type="GL - Journal Entry"))
        return False

    @staticmethod
    def check_lock_period_pos(resource, company_id, working_date):
        KgAccountPeriod.check_lock_period(
            resource, company_id, working_date,
            trx_type="is_pos_closed")

    @staticmethod
    def check_lock_period(resource, company_id, working_date, trx_type="is_ar_closed"):
        lock_period, message = KgAccountPeriod.get_period(resource, company_id, working_date)
        if lock_period:
            trx_type_info = MAP_TRX_TYPE_TO_MESSAGE.get(
                trx_type,
                trx_type.replace('is_', '').replace('_closed', '').upper())
            if getattr(lock_period, trx_type, False):
                raise UserError(message.format(
                    type=trx_type_info,
                ))

    @staticmethod
    def get_period(resource, company_id, working_date):
        lock_periods = resource.env['account.period'].search([
            ('company_id', '=', company_id),
            ('date_start', '<=', working_date),
            ('date_end', '>=', working_date),
        ])
        period_info = lock_periods[0].period_info if lock_periods else "this"
        message = _("You cannot add/modify entries on this date period, "
                    "{type} for " + period_info + " period already closed!")
        return lock_periods[0] if lock_periods else False, message

    @api.model
    def lock_last_month(self):
        date_val = parser.parse(fields.Date.context_today(self))
        date_val = date_val.replace(day=1)
        date_end = date_val.replace(month=date_val.month + 1) - timedelta(days=1)
        date_start = date_end.replace(day=1)
        period = date_start.strftime("%Y-%m-%d")
        name_part = period[:7]
        query = """
                insert into account_period (name, company_id, period, date_start, date_end,  
                is_gl_closed, is_ar_closed, is_ap_closed, is_pos_closed, is_bank_statement_closed,
                create_date, write_date) 
                select c.id || ':{name_part}' as name, c.id as company_id, '{period}' as period, 
                '{date_start}' as date_start, '{date_end}' as date_end,  
                true as is_gl_closed, true as is_ar_closed, true as is_ap_closed, 
                true as is_pos_closed, true as is_bank_statement_closed,
                now() as create_date, now() as write_date
                from res_company c left join account_period p on c.id = p.company_id
                    and p.period = '{period}'
                where p.id is null
            """.format(period=period, name_part=name_part,
                       date_start=date_start.isoformat(), date_end=date_end.isoformat())
        self._cr.execute(query)
        # self._cr.dictfetchall()
        return True


MAP_TRX_TYPE_TO_MESSAGE = {
    'is_ap_closed': 'AP/Internal Transfer'
}
