# -*- coding: utf-8 -*-
{
    'name': "Kompas Gramedia inventory",
    'summary': """inventory management for Kompas Gramedia.""",
    'description': """
        This module manages the followings:
            - Inventory management
    """,
    'author': "",
    'website': "",
    'category': 'Warehouse',
    'version': '10.0.0.0.1',
    'depends': [
                'stock',
                'kg_report_base',
    ],

    'data': [
        # 'security/ir.model.access.csv',
        # 'views/kg_res_partner.xml',
        # 'data/data_partner.xml',
         'wizards/picking_list_report_wizards.xml',
        # 'views/library_book.xml',
        'views/picking_list.xml',
        'views/product_view.xml',
        'reports/picking_list_report.xml',
    ],

    'demo': [

    ],

}
