from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError, ValidationError


class PayrollConfiguration(models.Model):
    _name = 'hr.kg.payroll.configuration'

    name = fields.Char(help='Payroll Setting Name')

    company_id = fields.One2many('res.company', 'payroll_config_id', help="Company Id")
    company_medical_percentage = fields.Float('Company BPJS (%)',
                                              help='Percentage medical for company')

    employee_medical_percentage = fields.Float('Employee BPJS (%)',
                                               help='Percentage medical for employee')

    medical_maxvalue = fields.Float('Medical Max Value',
                                    help='Max Value for medical')

    # BPJSTK Contribution
    work_accident_percentage = fields.Float('Company JKK(%)',
                                            help='Percentage work accident from company')

    life_insurance_percentage = fields.Float('Company JKM(%)',
                                             help='Percentage life insurance from company')

    pension_plan_company_percentage = fields.Float('Company JHT(%)',
                                                   help='Percentage pension plan from company')

    pension_plan_employee_percentage = fields.Float('Employee JHT(%)',
                                                    help='Percentage pension plan from employee')
    # Pension Contribution
    pension_guarantee_company_percentage = fields.Float('Company JP(%)',
                                                        help='Percentage pension guarantee from company')

    pension_guarantee_employee_percentage = fields.Float('Employee JP(%)',
                                                         help='Percentage pension guarantee from employee')

    pension_guarantee_max_value = fields.Float('Pension Max Value',
                                               help='Max value pension guarantee from employee')
    # UMP
    province_minimum_salary = fields.Float('Province Minimum Salary',
                                           help='Province Minimum Salary')

    #JSHK
    jshk_percentage = fields.Float('JSHK %', help='Jaminan Sosial dalam Hubungan Kerja')

    payroll_service_charge_id = fields.One2many('hr.kg.payroll.configuration.service.charge', 'payroll_config_id')
    payroll_family_id = fields.One2many('hr.kg.payroll.configuration.family', 'payroll_config_id')

    #DPLK
    company_dplk = fields.Float('Company DPLK(%)')
    employee_dplk = fields.Float('Employee DPLK(%)')

    #pph
    pph_percentage = fields.Float('Percentage(%)')


class ConfigurationServiceCharge(models.Model):
    _name = 'hr.kg.payroll.configuration.service.charge'

    payroll_config_id = fields.Many2one('hr.kg.payroll.configuration')

    year = fields.Selection([(num, str(num)) for num in range(2005, (datetime.now().year) + 10)], 'Year', default=datetime.now().year)

    max_value = fields.Float(help='Service Charge Maximal Value')


class PayrollConfigurationFamily(models.Model):
    _name = 'hr.kg.payroll.configuration.family'
    _rec_name = 'code'

    payroll_config_id = fields.Many2one('hr.kg.payroll.configuration')
    code = fields.Char('Family Status',
                              help='Family State')

    description = fields.Char('Description',
                              help='Family Description')

    percentage = fields.Float('Percentage',
                              help='Family Percentage')






