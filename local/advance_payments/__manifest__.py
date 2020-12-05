# -*- coding: utf-8 -*-
{
    'name': "Advance Payments KG",
    'version': '1.0.0',
    'summary': """
        Advance Payments on Invoices for Kompas Gramedia""",

    'description': """
        This module add some field in Advance Payments:
        Posting Date, Status Deposit, Guest Name, Remark, 
        Reff No, Reservation No
    """,

    'author': "Kompas Gramedia",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Invoice',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'account_payment_advance_mac5',
        'kg_account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/advance_payments.xml',
        'security/account_access_right.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
