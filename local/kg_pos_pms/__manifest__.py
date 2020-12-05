# -*- coding: utf-8 -*-
{
    'name': "KG POS - Working Date",

    'summary': """
        Synchronize working date PMS-POS
        """,

    'description': """ Synchronize between working date in POS with PMS 
    """,

    'author': "Kompas Gramedia",
    'website': "http://www.kompas.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Point of sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'kg_pos',
    ],

    # always loaded
    'data': [
        'views/pos_session_pms.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}