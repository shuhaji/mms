from odoo import api, fields, models
import calendar
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class Employee(models.Model):
    _inherit = 'hr.employee'

    npwp_no = fields.Char('NPWP No', size=15)
    bpjsks_no = fields.Char('BPJSKS No')
    bpjstk_no = fields.Char('BPJSTK No')
    bpjsks_join_date = fields.Date('BPJSKS Join Date')
    bpjstk_join_date = fields.Date('BPJSTK Join Date')
    work_location = fields.Many2one('hr.location')
    jshk_join_date = fields.Date('JSHK Join Date')
    dplk_join_date = fields.Date('DPLK Join Date')
    bank_id = fields.Many2one('res.bank')
    account_name = fields.Char('Account Name')
    account_number = fields.Char('Account Number')

    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    zip = fields.Char('Zip', change_default=True)
    city = fields.Char('City')
    state_id = fields.Many2one("res.country.state", string='State')
    country_id = fields.Many2one('res.country', string='Country')

    religion_id = fields.Many2one("hr.religion", string='Religion')
    tax_status_id = fields.Many2one("hr.kg.payroll.tax.ptkp", string='Tax Status')
    fam_status_id = fields.Many2one("hr.kg.payroll.configuration.family", string='Family Status')

    employee_id = fields.Char('Employee Id')
    month_employment_date = fields.Float(
        'Months of Employment',
        compute='_find_month_employment',
    )

    is_jshk = fields.Boolean(
        'JSHK',
        default=False,
        groups="hr.group_hr_user"
    )
    is_dplk = fields.Boolean(
        'DPLK',
        default=False,
        groups="hr.group_hr_user"
    )

    def get_day_work_hours_count(self, day_date, calendar=None):
        """Return 24 as work hours when detecting through context and weekday
        that the day passed is one of the rest days.
        """
        if self.env.context.get('include_rest_days') and calendar:
            real_weekdays = calendar.with_context(include_rest_days=False)._get_weekdays()
            if day_date.weekday() not in real_weekdays:
                return 24
        return super().get_day_work_hours_count(day_date, calendar=calendar)

    def _find_month_employment(self):
        for employee in self:
            initial_month = fields.Date.from_string(employee.initial_employment_date)

            if initial_month is None:
                employee.month_employment_date = 0
            else:
                month_number = initial_month.month
                employee.month_employment_date = month_number

    initial_employment_date = fields.Date(
        string='Initial Date of Employment',
        help='Date of first employment if it was before the start of the '
             'first contract in the system.',
    )
    length_of_service = fields.Float(
        'Months of Service',
        compute='_compute_months_service',
    )

    def _first_contract(self):
        hr_contract = self.env['hr.contract'].sudo()
        return hr_contract.search([('employee_id', '=', self.id)],
                                  order='date_start asc', limit=1)

    @staticmethod
    def check_next_days(date_to, date_from):
        if date_from.day != 1:
            return 0
        days_in_month = calendar.monthrange(date_to.year, date_to.month)[1]
        return 1 if date_to.day == days_in_month or \
                    date_from.day == date_to.day + 1 else 0

    @api.depends('contract_ids', 'initial_employment_date')
    def _compute_months_service(self):
        date_now = fields.Date.today()
        hr_contract = self.env['hr.contract'].sudo()
        for employee in self:
            nb_month = 0

            if employee.initial_employment_date:
                first_contract = employee._first_contract()
                if first_contract:
                    to_dt = fields.Date.from_string(first_contract.date_start)
                else:
                    to_dt = fields.Date.from_string(date_now)

                from_dt = fields.Date.from_string(
                    employee.initial_employment_date)

                nb_month += relativedelta(to_dt, from_dt).years * 12 + \
                            relativedelta(to_dt, from_dt).months + \
                            self.check_next_days(to_dt, from_dt)

            contracts = hr_contract.search([('employee_id', '=', employee.id)],
                                           order='date_start asc')
            for contract in contracts:
                from_dt = fields.Date.from_string(contract.date_start)
                if contract.date_end and contract.date_end < date_now:
                    to_dt = fields.Date.from_string(contract.date_end)
                else:
                    to_dt = fields.Date.from_string(date_now)
                nb_month += relativedelta(to_dt, from_dt).years * 12 + \
                            relativedelta(to_dt, from_dt).months + \
                            self.check_next_days(to_dt, from_dt)

            employee.length_of_service = nb_month

    @api.constrains('initial_employment_date', 'contract_ids')
    def _check_initial_employment_date(self):
        if self.initial_employment_date and self.contract_ids:
            initial_dt = fields.Date.from_string(self.initial_employment_date)
            first_contract_dt = fields.Date.from_string(
                self._first_contract().date_start)
            if initial_dt > first_contract_dt:
                raise ValidationError(_(
                    "The initial employment date "
                    "cannot be after the first "
                    "contract in the system!"))