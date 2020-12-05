# -*- coding: utf-8 -*-
{
    'name': "MMS Management System Support",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Shuhaji Taufiq",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
        'views/menu.xml',
        'views/course.xml',
        'views/permohonan_penilaiaan.xml',
        'views/pelaksana.xml',
        'views/hasil_penilaiaan.xml',
        'views/keputusan_sertifikasi.xml',
        'views/mms_res_partner.xml',
        'views/data_sertifikasi.xml',
        'views/data_auditor.xml',
        # 'views/partner.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}