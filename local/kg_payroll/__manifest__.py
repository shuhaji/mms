# -*- coding: utf-8 -*-
{
    'name': "Kompas Gramedia Payroll",
    'summary': """Payroll Costumization for Kompas Gramedia.""",
    'description': """
        This module manages the followings:
            - Hr
            - Invoice
    """,
    'author': "Ruby.h",
    'website': "http://www.rubyh.co",
    'category': 'Payroll',
    'version': '11.0.0.0.1',
    'depends': [
        'base',
        'hr',
        'kg_report_base',
        'hr_contract',
        'hr_payroll',
    ],

    'data': [
        'security/access_rights.xml',
        'security/ir.model.access.csv',
        'views/hr_employee_view.xml',
        'views/hr_contract_view.xml',
        'views/res_company_view.xml',
        'views/master_location_view.xml',
        'views/master_religion_view.xml',
        'views/payroll_configuration_view.xml',
        'views/tax_configuration_view.xml',
        'views/salary_rules_view.xml',
        'views/hr_kg_tax_notification_view.xml',
        'wizard/wizard_payslip_monthly_report.xml',
        'wizard/wizard_payslip_employee.xml',
        'views/hr_payslip.xml',
        'views/hr_holidays_status_views.xml',
        'views/hr_holidays_views.xml',
        'views/hr_holidays_views.xml',
        'wizard/hr_payslip_change_state_view.xml',
        'views/bank_transfer_request.xml',
    ],

    'demo': [

    ],

}
