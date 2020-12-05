import time
from unittest import TestCase

import odoo
from odoo import fields
from odoo.tools import float_compare, mute_logger, test_reports
from odoo.addons.point_of_sale.tests.common import TestPointOfSaleCommon


# @odoo.tests.common.at_install(False)
# @odoo.tests.common.post_install(True)


class TestPosHelpers(TestPointOfSaleCommon):

    def setUp(self):
        super(TestPosHelpers, self).setUp()
        self.env.user.company_id.hotel_id = 45

    def test_login_get_token(self):
        pos_helper = self.env['pos.helpers']
        base_url = "https://kg-pms-api-dev.azurewebsites.net"
        user_id = "ODOO_USER"
        password = "12345"
        hotel_id = "45"
        pms_token = pos_helper.get_token(
            base_url=base_url, user_id=user_id, user_password=password, hotel_id=hotel_id
        )
        self.assertTrue(pms_token, "Failed to get Access Token, it should not empty")

    def test_get_folio(self):
        pos_helper = self.env['pos.helpers']
        response = pos_helper.get_folio(
            room_number=102
        )
        # self.assertEqual(response.status_code, 200, 'PMS Response status code is not OK[200]')
        self.assertTrue(response, "Failed to get folio, it should not empty")
        self.assertTrue(response[0].get('FolioId', None), 'PMS Folio ID must be more then zero')

    def test_send_pos_daily_summary_to_pms_crm(self):
        # self.assertTrue(1 == 1)
        pos_helper = self.env['pos.helpers']
        self.assertTrue(pos_helper.send_pos_daily_summary_to_pms_crm('2019-09-03'))

    def test_post_payment(self):
        pos_helper = self.env['pos.helpers']
        response = pos_helper.get_folio(
            room_number=102
        )
        # self.assertEqual(response.status_code, 200, 'PMS Response status code is not OK[200]')
        self.assertTrue(response, "Failed to get folio, it should not empty")
        folio_id = response[0].get('FolioId', None)
        self.assertTrue(folio_id, 'PMS Folio ID must be more then zero')

        # I click on create a new session button
        self.pos_config.open_session_cb()

        # I create a PoS order with 2 units of PCSC234 at 450 EUR (Tax Incl)
        # and 3 units of PCSC349 at 300 EUR. (Tax Excl)
        pos_order_pos0 = self.PosOrder.create({
            'company_id': self.company_id,
            'folio_id': folio_id,
            'pricelist_id': self.partner1.property_product_pricelist.id,
            'partner_id': self.partner1.id,
            'lines': [(0, 0, {
                'name': "OL/0001",
                'product_id': self.product3.id,
                'price_unit': 450,
                'discount': 0.0,
                'qty': 2.0,
                'tax_ids': [(6, 0, self.product3.taxes_id.ids)],
            }), (0, 0, {
                'name': "OL/0002",
                'product_id': self.product4.id,
                'price_unit': 300,
                'discount': 0.0,
                'qty': 3.0,
                'tax_ids': [(6, 0, self.product4.taxes_id.ids)],
            })]
        })

        # test charge to Room (send payment data to PMS)
        response = pos_helper.post_payment(
            order=pos_order_pos0
        )
        self.assertEqual(response.status_code, 200, 'PMS Response status code is not OK[200]')

    def test_post_adv_payment(self):
        pos_helper = self.env['pos.helpers']
        response = pos_helper.get_folio(
            room_number=102
        )
        # self.assertEqual(response.status_code, 200, 'PMS Response status code is not OK[200]')
        self.assertTrue(response, "Failed to get folio, it should not empty")
        folio_id = response[0].get('FolioId', None)
        self.assertTrue(folio_id, 'PMS Folio ID must be more then zero')

        # I click on create a new session button
        self.pos_config.open_session_cb()

        # I create a PoS order with 2 units of PCSC234 at 450 EUR (Tax Incl)
        # and 3 units of PCSC349 at 300 EUR. (Tax Excl)
        pos_order_pos0 = self.PosOrder.create({
            'company_id': self.company_id,
            'folio_id': folio_id,
            'pricelist_id': self.partner1.property_product_pricelist.id,
            'partner_id': self.partner1.id,
            'lines': [(0, 0, {
                'name': "OL/0001",
                'product_id': self.product3.id,
                'price_unit': 450,
                'discount': 0.0,
                'qty': 2.0,
                'tax_ids': [(6, 0, self.product3.taxes_id.ids)],
            }), (0, 0, {
                'name': "OL/0002",
                'product_id': self.product4.id,
                'price_unit': 300,
                'discount': 0.0,
                'qty': 3.0,
                'tax_ids': [(6, 0, self.product4.taxes_id.ids)],
            })]
        })

        # TODO: get advance payment info
        # self.pos_order_pos0.pos_advance_payment_ids
        # TODO: test update balance advance deposit in PMS
        # response = pos_helper.post_adv_payment(
        #     adv_payment=None
        # )
        # self.assertEqual(response.status_code, 200, 'PMS Response status code is not OK[200]')


