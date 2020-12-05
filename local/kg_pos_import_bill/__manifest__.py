# -*- coding: utf-8 -*-
{
    'name': 'KG Pos Orders - Reservation',
    'version': '11.0.1.0.0',
    'summary': """POS Table Reservation""",
    'description': """Create Table Reservation and Load Reservation in POS""",
    'category': 'Point of Sale',
    'author': 'Rubyh.co',
    'company': 'Rubyh.co',
    'support': 'info@rubyh.co',
    'website': "",
    'depends': ['point_of_sale', 'pos_longpolling', 'pos_restaurant', 'eventtype'],
    'data': [
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/kg_pos_reservation.xml',
        'data/cron_pos_checkout.xml',
        'wizards/wizard_table_reservation_list_view.xml',
        'reports/report_table_reservation_list.xml',
        'wizards/wizard_table_productivities_view.xml',
        'reports/report_table_productivities.xml',
        'wizards/wizard_table_loss_view.xml',
        'reports/report_table_loss.xml',
        'wizards/wizard_cancel_reservation_view.xml',
        'views/kg_pos_banquet_event_order.xml',
        'views/function_room.xml',
        'security/pos_order_rule.xml',
    ],
    'images': ['static/description/copy_order_to_cart.gif'],
    'qweb': [
        "static/src/xml/pos_order_reservations.xml",
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}