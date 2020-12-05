# -*- coding: utf-8 -*-
{
    'name': "Shift KG",

    'summary': """
        Shift on Employees for Kompas Gramedia""",

    'description': """
        This module add Shift in Employees.
    """,

    'author': "Kompas Gramedia",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Employee',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'hr',
                'base_setup',
                ],


    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/shift.xml',
        'security/shift_security.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}