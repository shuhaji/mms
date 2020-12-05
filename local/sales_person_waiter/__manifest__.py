# -*- coding: utf-8 -*-
{
    'name': "sales_person_waiter",

    'summary': """
        As an admin, I'd like to mark employee as waiter and sales person""",

    'description': """
        As an admin, I'd like to maintain master data for sales person
        As an admin, I'd like to mark employee as waiter
    """,

    'author': "KG CITIS",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
