# -*- coding: utf-8 -*-
{
    'name': "Event Type KG",

    'summary': """
        Event Type in POS for Kompas Gramedia""",

    'description': """
        This module add Catalog Event Type in POS
    """,

    'author': "Kompas Gramedia",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Point of Sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/eventtype.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}