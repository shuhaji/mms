import base64
from io import StringIO

from dateutil import parser
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.exceptions import UserError


class BankTransferRequestPayroll(models.Model):
    _name = 'bank.transfer.request.payroll'
    _rec_name = 'company_id'

    name = fields.Char(string='Description')
    period = fields.Date(default=fields.Date.today, string="Period", required=True,
                         states={'confirmed': [('readonly', True)]})
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id.id)
    salary_structure = fields.Many2one('hr.payroll.structure', 'Structure', help='Salary Structure Payroll',
                                       required=True, copy=False, states={'confirmed': [('readonly', True)]})
    option = fields.Selection([("payslip", "Payslip"), ("input", "Input")], string='Option', required=True,
                              help='Select the data to be transferred', states={'confirmed': [('readonly', True)]})
    bank_id = fields.Many2one('res.bank', related='bank_account_id.bank_id', states={'confirmed': [('readonly', True)]})
    bank_account_id = fields.Many2one('res.partner.bank', string='Bank Account',
                                      ondelete='restrict', domain="[('company_id', '=', company_id)]",
                                      states={'confirmed': [('readonly', True)]})
    transfer_date = fields.Date(string='Transfer Date', default=fields.Date.today,
                                states={'confirmed': [('readonly', True)]})

    transfer_ids_input = fields.One2many('hr.payslip.input', 'transfer_request_id', string='Transfer id Payslip Input')
    transfer_ids_payslip = fields.One2many('hr.payslip', 'transfer_request_id_payslips', string='Transfer id Payslip')

    department_id = fields.Many2many('hr.department', string='Department',
                                     states={'confirmed': [('readonly', True)]})
    work_location = fields.Many2many('hr.location', groups="hr.group_hr_user",
                                     states={'confirmed': [('readonly', True)]})
    employee_id = fields.Many2many('hr.employee', string='Employee',
                                   states={'confirmed': [('readonly', True)]})

    _sql_constraints = [('unique_bank_product', 'unique(period, salary_structure)',
                         'The period and salary structure cannot be the same, check again')]
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed')], default='draft', states={'confirmed': [('readonly', True)]})

    file_name = fields.Char(default=False)
    file_binary = fields.Binary('File Binary', compute='generate_tax_file', default=False)
    binary_object_code = fields.Char(required=True)
    binary_object_code = fields.Char()

    date_from = fields.Date(string='Start Date', compute='filter_date_onchange', store=True,
                            states={'confirmed': [('readonly', True)]})
    date_to = fields.Date(string='End Date', compute='filter_date_onchange', store=True,
                          states={'confirmed': [('readonly', True)]})

    @api.one
    @api.depends('period')
    def filter_date_onchange(self):
        if self.period:
            date_from, date_to = self.set_period(self.period)
            self.update({
                "date_from": date_from,
                "date_to": date_to})

    @api.model
    def set_period(self, period):
        if period:
            date_val = parser.parse(period)
            date_from = date_val.replace(day=1) if date_val else False
            date_to = date_from + relativedelta(months=1, days=-1) if date_from else False
            return date_from, date_to
        else:
            return False, False

    @api.multi
    def button_confirm(self):
        bt_option = self.option
        update_option_payslip, where_employee_clause, where_department_clause, where_location_clause = self.query_get_clause2()
        if self.state == 'draft' or self.binary_object_code is None:
            self.file_name = "binary_file-{comp_id}-{period}.txt".format(
                comp_id=self.company_id.id,
                period=self.period[0:7]
            )
            self.state = 'confirmed'
            query = """  
            """ + update_option_payslip + """
                and p.company_id='{company_id}'
                and (p.date_from >= '{date_from}'AND p.date_to <= '{date_to}') 
                """ + where_department_clause + """
                """ + where_location_clause + """
                """ + where_employee_clause + """
            """
            query += " AND p.struct_id = {structure_id}".format(structure_id=self.salary_structure.id) \
                if self.salary_structure.id else ''

            final_query = query.format(company_id=self.company_id.id,
                                       date_from=self.date_from,
                                       date_to=self.date_to,
                                       bank_transfer_request_id=self.id,
                                       bt_option=bt_option)
            self.env.cr.execute(final_query)

        else:
            raise UserError('Please Check Bank Transfer State.')

    def query_get_clause2(self):
        update_option_payslip = ""
        if self.option == 'payslip':
            update_option_payslip = """ 
                update hr_payslip
                    set transfer_request_id_payslips = '{bank_transfer_request_id}'
                from hr_payslip p
                inner join hr_employee e on e.id = p.employee_id
                where p.state='done'
                """
        elif self.option == 'input':
            update_option_payslip = """
                update hr_payslip_input pl
                    set transfer_request_id = '{bank_transfer_request_id}'
                from hr_payslip p
                inner join hr_employee e on e.id = p.employee_id
                where pl.payslip_id = p.id and p.state='done'
                """

        where_department_clause = ""
        if self.department_id:
            where_department_clause = "and e.department_id {operator}{depart_ids}".format(
                operator='=' if len(self.department_id.ids) == 1 else "in ",
                depart_ids=self.department_id.ids[0]
                if len(self.department_id.ids) == 1 else tuple(self.department_id.ids))

        where_employee_clause = ""
        if self.employee_id:
            where_employee_clause = "and p.employee_id {operator} {emp_ids}".format(
                operator='=' if len(self.employee_id.ids) == 1 else "in ",
                emp_ids=self.employee_id.ids[0]
                if len(self.employee_id) == 1 else tuple(self.department_id.ids))

        where_location_clause = ""
        if self.work_location:
            where_location_clause = "and e.work_location {operator}{loc_ids}".format(
                operator='=' if len(self.work_location.ids) == 1 else "in ",
                loc_ids=self.work_location.ids[0]
                if len(self.work_location) == 1 else tuple(self.department_id.ids))

        return update_option_payslip, where_employee_clause, where_department_clause, where_location_clause

    @api.multi
    @api.depends('file_name')
    def generate_tax_file(self):
        where_department_clause, where_employee_clause, where_location_clause = self.query_get_clause()

        depart_ids = tuple(self.department_id.ids)
        if len(self.department_id.ids) == 1:
            depart_ids = (self.department_id.ids[0])

        emp_ids = tuple(self.employee_id.ids)
        if len(self.employee_id.ids) == 1:
            emp_ids = (self.employee_id.ids[0])

        loc_ids = tuple(self.work_location.ids)
        if len(self.work_location.ids) == 1:
            loc_ids = (self.work_location.ids[0])

        file_content = ""
        if self.file_name and self.state == 'confirmed':
            query = """
            select  e."name" as employee_name
                            , p.netto as transfer_amount_nett
                            , e.employee_id as NIK
                            , '' as department_code
                            , e.account_number
                            , c.company_code
                            , bt.transfer_date
                        from bank_transfer_request_payroll bt
                        left join hr_payslip  p on bt.id = p.transfer_request_id_payslips
                        left join res_company c on c.id = bt.company_id
                        left join hr_employee e on e.id = p.employee_id
                        where p.company_id= '{company_id}' 
                        and p.state='done'
                        and (p.date_from >= '{date_from}'and p.date_to <= '{date_to}') 
                        and p.struct_id = '{structure_id}'
                        """ + where_department_clause + """
                        """ + where_location_clause + """
                        """ + where_employee_clause + """
                        
                        union
                        select  e."name" as employee_name
                            , pi.amount as tramsfer_amount_nett
                            , e.employee_id as NIK
                            , '' as department_code
                            , e.account_number
                            , c.company_code
                            , bt.transfer_date
                        from bank_transfer_request_payroll bt
                        left join hr_payslip_input pi on bt.id = pi.transfer_request_id
                        left join hr_payslip  p on pi.payslip_id = p.id
                        left join res_company c on c.id = bt.company_id
                        left join hr_employee e on e.id = p.employee_id
                        where p.company_id= '{company_id}' 
                        and p.state='done'
                        and (p.date_from >= '{date_from}'and p.date_to <= '{date_to}') 
                        and p.struct_id = '{structure_id}'
                        """ + where_department_clause + """ 
                        """ + where_location_clause + """
                        """ + where_employee_clause + """
                        
            """
            final_query = query.format(company_id=self.company_id.id,
                                       date_from=self.date_from,
                                       date_to=self.date_to,
                                       structure_id=self.salary_structure.id,
                                       depart_ids=depart_ids,
                                       emp_ids=emp_ids,
                                       loc_ids=loc_ids)
            self.env.cr.execute(final_query)
            cs = self.env.cr.dictfetchall()

            stream_out = StringIO()
            default = "{default}".format(default='00000000000')
            company_code = "0000000000000{company_code}".format(company_code=self.company_id.company_code or '')[-13:]
            date_transfer_date = "{date_transfer_date}".format(date_transfer_date=self.period[8:10])
            default2 = "{default2}".format(default2='01')
            bank_account_id = "0000000000{bank_account_id}".format(bank_account_id=self.bank_account_id.acc_number)[
                              -10:]
            default3 = "{default3}".format(default3='11')
            default4 = "{default4}".format(default4='MF')
            employee_count = "00000{employee_count}".format(employee_count=len(cs) or '')[-5:]
            total_salary_employee = "00000000000000{total_salary_employee}.00".format(
                total_salary_employee=sum(amount['transfer_amount_nett'] for amount in cs) or '')[-17:]
            month_transfer_date = "{month_transfer_date}".format(month_transfer_date=self.period[5:7])
            year_transfer_date = "{year_transfer_date}".format(year_transfer_date=self.period[0:4])

            stream_out.write(
                "{default}{company_code}{date_transfer_date}{default2}{bank_account_id}{default3}{default4}"
                "{employee_count}{total_salary_employee}{month_transfer_date}{year_transfer_date}"
                    .format(default=default, company_code=company_code, date_transfer_date=date_transfer_date,
                            default2=default2, bank_account_id=bank_account_id, default3=default3, default4=default4,
                            employee_count=employee_count, total_salary_employee=total_salary_employee,
                            month_transfer_date=month_transfer_date, year_transfer_date=year_transfer_date))
            for row in cs:
                default5 = "{default5}".format(default5='0')
                account_number = "0000000000{account_number}".format(account_number=row.get('account_number') or '')[
                                 -10:]
                transfer_amount_nett = "000000000000000{transfer_amount_nett}".format(
                    transfer_amount_nett=row.get('transfer_amount_nett') or '')[-15:]
                nik = "0000000000{nik}".format(nik=row.get('nik') or '')[-10:]
                employee_name = "{employee_name}".format(employee_name=row.get('employee_name')[-30:])
                department_code = "{department_code}".format(department_code=row.get('department_code'))

                stream_out.write("\n")
                stream_out.write(
                    "{default5}{account_number}{transfer_amount_nett}{nik}{employee_name}{department_code}".format(
                        default5=default5, account_number=account_number, transfer_amount_nett=transfer_amount_nett,
                        nik=nik, employee_name=employee_name, department_code=department_code))

            file_content = stream_out.getvalue()
        self.update({'file_binary': base64.b64encode(bytes(file_content, "utf-8"))})

    def query_get_clause(self):

        where_department_clause = ""
        if self.department_id:
            where_department_clause = "and e.department_id in {depart_ids}"
            if len(self.department_id.ids) == 1:
                where_department_clause = "and e.department_id = {depart_ids}"

        where_employee_clause = ""
        if self.employee_id:
            where_employee_clause = "and p.employee_id in {emp_ids}"
            if len(self.employee_id.ids) == 1:
                where_employee_clause = "and p.employee_id = {emp_ids}"

        where_location_clause = ""
        if self.work_location:
            where_location_clause = "and e.work_location in {loc_ids}"
            if len(self.work_location.ids) == 1:
                where_location_clause = "and e.work_location = {loc_ids}"

        return where_department_clause, where_employee_clause, where_location_clause
