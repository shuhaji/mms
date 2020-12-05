# -*- coding: utf-8 -*-
{
    'name': "Kompas Gramedia Tax",
    'summary': """Tax Costumization for Kompas Gramedia.""",
    'description': """
        This module manages the followings:
            - Tax
    """,
    'author': "",
    'website': "",
    'category': 'Tax Category',
    'version': '10.0.0.0.1',
    'depends': [
        'base',
        
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/kg_tax_category.xml',
        'data/kg_tax_category_data.xml',
    ],
    'demo': [

    ],

    'qweb' : [
        # 'static/src/xml/pos.xml',
    ],
}
