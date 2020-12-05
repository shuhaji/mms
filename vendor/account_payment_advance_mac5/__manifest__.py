# -*- coding: utf-8 -*-
{
    'name': 'Advance Payments',
    'version': '11.0.2.0.1',
    'summary': 'Advance Payments on Invoices',
    'description': """
Advance Payments
================

This module creates advance payments with corresponding advance payment account. If advance payment
is applied to an invoice, it will create another Journal Entry for advance payment account and
partner's receivable/payable account.


Keywords: Customer Invoice Advance Payments, Vendor Invoice Advance Payments,
Vendor Bill Advance Payments, Supplier Invoice Advance Payments, Odoo Advance Payments,
Odoo Advance Deposits
""",
    'category': 'Accounting',
    'author': 'MAC5',
    'contributors': ['Michael Aldrin C. Villamar'],
    'website': 'https://apps.odoo.com/apps/modules/browse?author=MAC5',
    'depends': ['account'],
    'data': [
        'wizard/account_advance_payment_invoice_views.xml',
        'views/res_config_views.xml',
        'views/account_payment_views.xml',
        'views/account_invoice_views.xml',
        'views/report_invoice.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'images': [
        'static/description/apply_adv_payment_invoice2.png',
        'static/description/apply_adv_payment_invoice3.png',
        'static/description/apply_adv_payment_invoice4.png',
        'static/description/apply_adv_payment_invoice5.png',
        'static/description/apply_adv_payment_invoice.png',
        'static/description/invoice_report.png',
    ],
    'price': 199.99,
    'currency': 'EUR',
    'support': 'macvillamar@live.com',
    'license': 'OPL-1',
}
