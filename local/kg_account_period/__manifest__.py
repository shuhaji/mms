# -*- coding: utf-8 -*-
{
    'name': "Kompas Gramedia Account Period",
    'summary': """Account Period Locking for Kompas Gramedia.""",
    'description': """
        This module manages Accounting Period (Lock or Not) for the followings:
            - Account
            - Point of Sale
    """,
    'author': "CITIS KG",
    'website': "",
    'category': 'Account',
    'version': '11.0.0.0.2',
    'depends': [
        'account',
        'point_of_sale'
    ],
    'data': [
        'data/cron_account_period_lock_last_month.xml',
        'views/account_period.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
    ],
}
