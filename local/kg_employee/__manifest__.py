# -*- coding: utf-8 -*-
{
    'name': "Kompas Gramedia Employee",
    'summary': """Employee Costumization for Kompas Gramedia.""",
    'description': """
        This module manages the followings:
            - Hr
    """,
    'author': "",
    'website': "",
    'category': 'Base',
    'version': '10.0.0.0.1',
    'depends': [
        'base',
        'hr',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/kg_hr_employee.xml',
        'views/templates.xml',
    ],

    'demo': [

    ],

}
