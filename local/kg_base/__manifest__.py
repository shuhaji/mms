# -*- coding: utf-8 -*-
{
    'name': "Kompas Gramedia Base",
    'summary': """Base Costumization for Kompas Gramedia.""",
    'description': """
        This module manages the followings:
            - Base
    """,
    'author': "",
    'website': "",
    'category': 'Base',
    'version': '10.0.0.0.1',
    'depends': [
        'base'
    ],

    'data': [
        # 'security/ir.model.access.csv',
        'views/kg_res_partner.xml',
        'data/data_partner.xml',
        'data/data_master_config_api.xml',
        'views/kg_res_bank.xml',
    ],

    'demo': [

    ],

}
