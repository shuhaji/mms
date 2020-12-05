# -*- coding: utf-8 -*-
{
    'name': "Kompas Gramedia Purchase",

    'summary': """
        Purchase Customization for Kompas Gramedia""",

    'description': """
        This module add KG Purchase
    """,

    'author': "Kompas Gramedia",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Purchase',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['purchase',
                'purchase_request'
                ],


    # always loaded
    'data': [
        'security/purchase_access_rights.xml',
        'security/ir.model.access.csv',
        # 'data/purchase_request_sequence.xml',
        'data/purchase_order_tier_definition.xml',
        'views/purchase_type.xml',
        'views/purchase_request_view.xml',
        'views/purchase_order_view.xml',
        'views/purchase_order_tier_validation_view.xml',
        'views/stock_request_order_tier_validation_view.xml',
        'views/stock_request_view.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}