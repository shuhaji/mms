import time
from datetime import datetime

import odoo
from odoo import fields
from odoo.tools import float_compare, mute_logger, test_reports
from odoo.addons.point_of_sale.tests.common import TestPointOfSaleCommon

# @odoo.tests.common.at_install(False)
# @odoo.tests.common.post_install(True)


class TestPosReservation(TestPointOfSaleCommon):

    def setUp(self):
        super(TestPosReservation, self).setUp()
        self.create_pos_reservation_dummy_data()
        self.env.user.company_id.hotel_id = 45

    def test_new_order_table_but_definite_already_exists(self):
        self.pos_res2 = self.env['kg.pos.order.reservation'].create({
            'reservation_pos_id': self.pos_config.id,
            'state_reservation': 'tentative',
            'reservation_time_start': '2019-05-01 01:00:00',
            'reservation_time_end': '2019-05-01 09:00:00',
            'table_list': [(0, 0, {
                'table_id': self.table1.id,
            }), ]
        })

        self.assertEqual(self.pos_res2.state_reservation, 'waiting_list',
                         "Order Reservation should be waiting list")

    def test_change_order_table(self):
        # ubah table meja jadi T3
        for table in self.pos_res1.table_list:
            table.write({'table_id': self.table3.id})

        self.assertEqual(self.pos_res_wl_2.state_reservation, 'tentative',
                         "Order Reservation should be tentative")
        self.assertEqual(self.pos_res_wl_1.state_reservation, 'waiting_list',
                         "Order Reservation should be tentative")
        self.assertEqual(self.pos_res_wl_3.state_reservation, 'waiting_list',
                         "Order Reservation should be tentative")

    def create_pos_reservation_dummy_data(self):
        self.table1 = self.env['restaurant.table'].create({
            'name': 'T1',
            'shape': 'square',
        })
        self.table2 = self.env['restaurant.table'].create({
            'name': 'T2',
            'shape': 'square',
        })
        self.table3 = self.env['restaurant.table'].create({
            'name': 'T3',
            'shape': 'square',
        })
        self.pos_res1 = self.env['kg.pos.order.reservation'].create({
            'reservation_pos_id': self.pos_config.id,
            'state_reservation': 'definite',
            'reservation_time_start': '2019-05-01 02:00:00',
            'reservation_time_end': '2019-05-01 05:00:00',
            'table_list':  [(0, 0, {
                'is_waiting_list': False,
                'table_id': self.table1.id,
            }), ]
        })

        self.pos_res_wl_1 = self.env['kg.pos.order.reservation'].create({
            'reservation_pos_id': self.pos_config.id,
            'state_reservation': 'waiting_list',
            'reservation_time_start': '2019-05-01 01:00:00',
            'reservation_time_end': '2019-05-01 03:00:00',
            'table_list': [(0, 0, {
                'is_waiting_list': True,
                'table_id': self.table1.id,
            }), (0, 0, {
                'is_waiting_list': True,
                'table_id': self.table2.id,
            })]
        })
        self.pos_res_wl_2 = self.env['kg.pos.order.reservation'].create({
            'reservation_pos_id': self.pos_config.id,
            'state_reservation': 'waiting_list',
            'reservation_time_start': '2019-05-01 03:00:00',
            'reservation_time_end': '2019-05-01 04:00:00',
            'table_list': [(0, 0, {
                'is_waiting_list': True,
                'table_id': self.table1.id,
            }), ]
        })
        self.pos_res_wl_3 = self.env['kg.pos.order.reservation'].create({
            'reservation_pos_id': self.pos_config.id,
            'state_reservation': 'waiting_list',
            'reservation_time_start': '2019-05-01 03:00:00',
            'reservation_time_end': '2019-05-01 06:00:00',
            'table_list': [(0, 0, {
                'is_waiting_list': True,
                'table_id': self.table1.id,
            }), ]
        })
        self.pos_res_tbl2 = self.env['kg.pos.order.reservation'].create({
            'reservation_pos_id': self.pos_config.id,
            'state_reservation': 'definite',
            'reservation_time_start': '2019-05-01 02:00:00',
            'reservation_time_end': '2019-05-01 05:00:00',
            'table_list': [(0, 0, {
                'is_waiting_list': False,
                'table_id': self.table2.id,
            }), ]
        })

        self.pos_res_non_1 = self.env['kg.pos.order.reservation'].create({
            'reservation_pos_id': self.pos_config.id,
            'state_reservation': 'waiting_list',
            'reservation_time_start': '2019-05-01 01:00:00',
            'reservation_time_end': '2019-05-01 01:30:00',
            'table_list': [(0, 0, {
                'is_waiting_list': True,
                'table_id': self.table1.id,
            }), ]
        })



