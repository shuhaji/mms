# Copyright 2015 Alessandro Camilli (<http://www.openforce.it>)
# Copyright 2019 Giovanni - GSLabIt
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Withholding Tax',
    'version': '11.0.1.0.2',
    'category': 'Account',
    'author': 'Openforce, Odoo Italia Network, '
              'Odoo Community Association (OCA)',
    'website': 'https://www.odoo-italia.net/',
    'license': 'AGPL-3',
    "depends": ['account'],
    "data": [
        'views/account.xml',
        'views/withholding_tax.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
    ],
    "installable": True
}
