from odoo import api, fields, models, http
from datetime import datetime, timedelta


class WizardKgPayrollPayslipMonthlyReport(models.TransientModel):
    _inherit = ['wizard.kg.report.base']
    _name = 'wizard.kg.report.payslip_monthly_report'
    _title = "KG Report - Payslip Monthly Report"

    date_from = fields.Date(string='Period Date', default=fields.Date.today)
    structure = fields.Selection(
        [('2', 'Gross'),
         ('3', 'Gross Up'),
         ],
        string='Select Structure',
        default='2')

    @api.multi
    def _get_data(self):
        """ get data from database or any other source

        :return: dict or list of dict
        """
        # extract financial report data
        now = datetime.utcnow()+timedelta(hours=7)
        get_payslip_monthly_report = self.get_payslip_monthly_report()
        blank_name = "..........................."
        self.report_has_logo = False  # sample report has logo
        data = {
            "config": {
                "date_from": self.date_from,
                "company_name": self.env.user.company_id.name,
                "prepared_by": self.env.user.name or blank_name,
                "print_date": now.strftime("%Y-%m-%d %H:%M"),
                "structure": self.structure,
            },
            "data": get_payslip_monthly_report
        }

        # return self._sample_data_reg_card()
        return data

    @api.multi
    def get_payslip_monthly_report(self):
        # get pos transaction data for Daily Card Report
        month = datetime.strptime(self.date_from, '%Y-%m-%d').strftime('%m')
        year = datetime.strptime(self.date_from, '%Y-%m-%d').strftime('%Y')
        query = """select * FROM
        (select a.id as payslip_id, a.employee_id,a.date_from, b.name as employee_name,
        b.npwp_no,b.initial_employment_date, c.name as job_name, 
        d.name as department_name,b.initial_employment_date,
        case
        when b.marital = 'married' then CONCAT('K',b.children)
        else 'TK'
        end as tax_status
        from hr_payslip a
        left join hr_employee b on a.employee_id=b.id
        left join hr_job c on b.job_id=c.id
        left join hr_department d on b.department_id=d.id
        left join hr_contract e on b.id=e.employee_id
        where EXTRACT(MONTH FROM a.date_from) = {month} and EXTRACT(year FROM a.date_from) = {year}
        and e.struct_id={structure}
        ) as ab
        LEFT JOIN
        (select
            a.slip_id, a.employee_id,
            sum(case when a.code = 'BASIC' then amount else 0 end) as BASIC,
            sum(case when a.code = 'trans' then amount else 0 end) as trans,
            sum(case when a.code = 'food' then amount else 0 end) as food,
            sum(case when a.code = 'ALJP' then amount else 0 end) as ALJP,
            sum(case when a.code = 'mk' then amount else 0 end) as mk,
            sum(case when a.code = 'kumulatif' then amount else 0 end) as kumulatif,
            sum(case when a.code = 'PTKP' then amount else 0 end) as PTKP,
            sum(case when a.code = 'jht1' then amount else 0 end) as jht1,
            sum(case when a.code = 'unpaid' then amount else 0 end) as unpaid,
            sum(case when a.code = 'ALJHT' then amount else 0 end) as ALJHT,
            sum(case when a.code = 'monthlytax1' then amount else 0 end) as monthlytax1,
            sum(case when a.code = 'monthlytax2' then amount else 0 end) as monthlytax2,
            sum(case when a.code = 'tax1' then amount else 0 end) as tax1,
            sum(case when a.code = 'tax2' then amount else 0 end) as tax2,
            sum(case when a.code = 'ALBPJS' then amount else 0 end) as ALBPJS,
            sum(case when a.code = 'ALJKK' then amount else 0 end) as ALJKK,
            sum(case when a.code = 'NET' then amount else 0 end) as NET,
            sum(case when a.code = 'DEJP' then amount else 0 end) as DEJP,
            sum(case when a.code = 'DEJKK' then amount else 0 end) as DEJKK,
            sum(case when a.code = 'DEBPJS' then amount else 0 end) as DEBPJS,
            sum(case when a.code = 'DEJPEMP' then amount else 0 end) as DEJPEMP,
            sum(case when a.code = 'alpph' then amount else 0 end) as alpph,
            sum(case when a.code = 'BJ1' then amount else 0 end) as BJ1,
            sum(case when a.code = 'jht2' then amount else 0 end) as jht2,
            sum(case when a.code = 'ALBCOMP' then amount else 0 end) as ALBCOMP,
            sum(case when a.code = 'GROSSTAX1' then amount else 0 end) as GROSSTAX1,
            sum(case when a.code = 'DEJKM' then amount else 0 end) as DEJKM,
            sum(case when a.code = 'DEJHTEMP' then amount else 0 end) as DEJHTEMP,
            sum(case when a.code = 'net1' then amount else 0 end) as net1,
            sum(case when a.code = 'pkp2' then amount else 0 end) as pkp2,
            sum(case when a.code = 'GROSS' then amount else 0 end) as GROSS,
            sum(case when a.code = 'ALJKM' then amount else 0 end) as ALJKM,
            sum(case when a.code = 'BJ2' then amount else 0 end) as BJ2,
            sum(case when a.code = 'mobi' then amount else 0 end) as mobi,
            sum(case when a.code = 'GROSSTAX3' then amount else 0 end) as GROSSTAX3,
            sum(case when a.code = 'DEBEMP' then amount else 0 end) as DEBEMP,
            sum(case when a.code = 'pkp1' then amount else 0 end) as pkp1,
            sum(case when a.code = 'DEBCOMP' then amount else 0 end) as DEBCOMP,
            sum(case when a.code = 'DEJHT' then amount else 0 end) as DEJHT,
            sum(case when a.code = 'net2' then amount else 0 end) as net2,
            sum(case when a.code = 'accom' then amount else 0 end) as accom,
            sum(case when a.code = 'taxdaily' then amount else 0 end) as taxdaily,
            sum(case when a.code = 'GROSSTAX2' then amount else 0 end) as GROSSTAX2,
            sum(case when a.code = 'BJ3' then amount else 0 end) as BJ3,
            sum(case when a.code = 'net3' then amount else 0 end) as net3,
            sum(case when a.code = 'pkp3' then amount else 0 end) as pkp3
        from hr_payslip_line a
        group by a.slip_id, a.employee_id
        order by a.slip_id) as x
        on ab.payslip_id = x.slip_id""".format(month=month, year=year, structure=self.structure)
        self.env.cr.execute(query)
        payslip_monthly_summary = self.env.cr.dictfetchall()

        return payslip_monthly_summary

    @staticmethod
    def _define_report_name():
        return "/kg_payroll/static/rpt/PayslipMonthly.mrt"
