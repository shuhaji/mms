# -*- coding: utf-8 -*-
{
    'name': "KG CITIS: Inventory-Stock",

    'summary': """ Inventory-Stock, Corporate IT & IS, Kompas Gramedia""",

    'description': """
        
    """,

    'author': "KG-CITIS",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Warehouse',
    'version': '11.0.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['stock',
                ],


    # always loaded
    'data': [
        'reports/picking_list_report.xml'
    ],
    "auto_install": False,
    "installable": True,
    "application": True,
    # only loaded in demonstration mode
    'demo': [
    ],
}