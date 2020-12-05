# -*- coding: utf-8 -*-
{
    'name': "Kompas Gramedia Product",
    'summary': """Product Costumization for Kompas Gramedia.""",
    'description': """
        This module manages the followings:
            - Product
    """,
    'author': "",
    'website': "",
    'category': 'Product',
    'version': '10.0.0.0.1',
    'depends': [
        'product',
        'kg_tax',
        'point_of_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/kg_product.xml',
        'views/product_filter_rule.xml',
        'views/product_category.xml',

    ],
    'demo': [

    ],

    'qweb': [
        # 'static/src/xml/pos.xml',
    ],
}
