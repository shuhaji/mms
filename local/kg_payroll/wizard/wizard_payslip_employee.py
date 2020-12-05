from odoo import api, fields, models, http
from datetime import datetime, timedelta


class WizardKgPayrollPayslipEmployee(models.TransientModel):
    _inherit = ['wizard.kg.report.base']
    _name = 'wizard.kg.report.payslip_employee'
    _title = "KG Report - Payslip Employee"

    date_from = fields.Date(string='Start Period Date', default=fields.Date.today)
    location_ids = fields.Many2many('hr.location', string='Location')
    structure_ids = fields.Many2many('hr.payroll.structure', string='Payslip Structure')
    department_ids = fields.Many2many('hr.department', string='Department')
    employee_ids = fields.Many2many('hr.employee', string='Employee')
    company_id = fields.Many2one('res.company',
                                 'Company',
                                 help="Company Id",
                                 default=lambda self: self.env.user.company_id.id)
    template = fields.Selection(
        [(1, 'Payslip Type 1'),
         (2, 'Payslip Type 2')
         ],
        string='Select Templates',
        default=1)

    @api.multi
    def _define_report_name(self):
        if self.template == 2:
            return "/kg_payroll/static/rpt/PayslipEmployee2.mrt"
        else:
            return "/kg_payroll/static/rpt/PayslipEmployee.mrt"

    @api.multi
    def _get_data(self):
        """ get data from database or any other source

        :return: dict or list of dict
        """
        # extract financial report data
        now = datetime.utcnow()+timedelta(hours=7)

        get_payslip_employee = self.get_payslip_employee()
        blank_name = "..........................."
        self.report_has_logo = False  # sample report has logo
        data = {
            "config": {
                "date_from": self.date_from,
                "company_name": self.env.user.company_id.name,
                "compiler": self.env.user.name,
                "template": self.template,
                "print_date": now.strftime("%Y-%m-%d"),

            },
            "data": get_payslip_employee
        }

        # return self._sample_data_reg_card()
        return data

    @api.multi
    def get_payslip_employee(self):
        where_department_clause, where_employee_clause, where_structure_clause, where_location_clause = self.query_get_clause()
        # get pos transaction data for Daily Card Report
        month = datetime.strptime(self.date_from, '%Y-%m-%d').strftime('%m')
        year = datetime.strptime(self.date_from, '%Y-%m-%d').strftime('%Y')
        depart_ids = tuple(self.department_ids.ids)
        if len(self.department_ids.ids) == 1:
            depart_ids = (self.department_ids.ids[0])
        emp_ids = tuple(self.employee_ids.ids)

        if len(self.employee_ids.ids) == 1:
            emp_ids = (self.employee_ids.ids[0])

        struct_ids = tuple(self.structure_ids.ids)
        if len(self.structure_ids.ids) == 1:
            struct_ids = (self.structure_ids.ids[0])

        loc_ids = tuple(self.location_ids.ids)
        if len(self.location_ids.ids) == 1:
            loc_ids = (self.location_ids.ids[0])

        query = """select case when sr.type_id = 'VAR' then 2 else 1 end as group_1,
                case when sr.type_id= 'VAR' then 'Penerimaan Tidak Tetap' else 'Penerimaan Tetap' end as group_1_name,
                case when src.code in ('DED','PPH21_REG','PPH21_IREG') then 1 else 2 end as group_2,
                case when src.code in ('DED','PPH21_REG','PPH21_IREG') then 'Potongan' else 'Penerimaan' end as group_2_name,
                e.employee_id, e."name" as emp_name, cf.code as fam_code, tp.tax_state, 
                l.code, l.total, l.name, d.name as dept_name, l.slip_id, p.date_from, p.date_to, l.sequence
                from hr_payslip_line l
                left join hr_salary_rule sr on sr.id = l.salary_rule_id
                left join hr_salary_rule_category src on sr.category_id = src.id
                left join hr_payslip p on l.slip_id = p.id
                left join hr_employee e on p.employee_id = e.id
                left join hr_department d on e.department_id = d.id
                left join hr_kg_payroll_configuration_family cf on cf.id = e.fam_status_id
                left join hr_kg_payroll_tax_ptkp tp on tp.id = e.tax_status_id
                where p.state = 'done' and sr.appears_on_payslip is true and p.company_id = {company_id}
                """+where_department_clause+""" """+where_employee_clause+""" """+where_structure_clause+"""
                """+where_location_clause+""" and l.total != 0
                and extract(month from p.date_to) = {month} and extract(year from p.date_to) = {year}
                order by slip_id, group_1_name, group_2_name desc, l.sequence"""

        final_query = query.format(month=month, year=year, company_id=self.company_id.id, depart_ids=depart_ids, emp_ids=emp_ids,
                    struct_ids=struct_ids, loc_ids=loc_ids)

        self.env.cr.execute(final_query)
        payslip_employee_summary = self.env.cr.dictfetchall()

        return payslip_employee_summary

    def query_get_clause(self):
        where_department_clause = ""
        if self.department_ids:
            where_department_clause = "and e.department_id in {depart_ids}"
            if len(self.department_ids.ids) == 1:
                where_department_clause = "and e.department_id = {depart_ids}"

        where_employee_clause = ""
        if self.employee_ids:
            if self.employee_ids:
                where_employee_clause = "and p.employee_id in {emp_ids}"
                if len(self.employee_ids.ids) == 1:
                    where_employee_clause = "and p.employee_id = {emp_ids}"

        where_structure_clause = ""
        if self.structure_ids:
            if self.structure_ids:
                where_structure_clause = "and p.struct_id in {struct_ids}"
                if len(self.structure_ids.ids) == 1:
                    where_structure_clause = "and p.struct_id = {struct_ids}"

        where_location_clause = ""
        if self.location_ids:
            if self.location_ids:
                where_location_clause = "and p.struct_id in {loc_ids}"
                if len(self.location_ids.ids) == 1:
                    where_location_clause = "and p.struct_id = {loc_ids}"

        return where_department_clause, where_employee_clause, where_structure_clause, where_location_clause


