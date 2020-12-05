import time
from datetime import datetime

import odoo
from odoo import fields
from odoo.tools import float_compare, mute_logger, test_reports
from odoo.addons.point_of_sale.tests.common import TestPointOfSaleCommon
from odoo.addons.kg_pos.controllers.kg_tax_online_export import KgApiTaxOnlineExport

# @odoo.tests.common.at_install(False)
# @odoo.tests.common.post_install(True)


class TestKgTaxOnline(TestPointOfSaleCommon):

    def setUp(self):
        super(TestKgTaxOnline, self).setUp()
        self.create_pos_dummy_data()
        self.env.user.company_id.hotel_id = 45

    def test_get_data(self):
        tax_online = KgApiTaxOnlineExport()
        # self.env.user.company_id.id
        data = tax_online.get_data(
            env=self.env,
            company_id=self.company_id, pos_date=self.pos_order_session0.working_date
        )
        self.assertTrue(data, "Failed to get tax online data, it should not empty")

    def create_pos_dummy_data(self):
        self.pos_order_session0.write({
            'start_at': datetime.now(),
        })
        self.tax_category1 = self.env['tax.category'].search([
            ('tax_code', '=', 'ATM')
        ])
        Tax = self.env['account.tax']
        self.tax_service = Tax.create({
            'sequence': 2,
            'name': 'Service 10 perc Incl',
            'amount_type': 'percent',
            'amount': 10.0,
            'price_include': 1,
            'include_base_amount': True
        })
        self.account_tax_10_incl = Tax.search([('name', '=', 'VAT 10 perc Incl')])

        self.product3.write({
            'list_price': 121,
            'tax_category_id': self.tax_category1.id,
            'taxes_id': [(6, 0, [self.tax_service.id, self.account_tax_10_incl.id])]
        })
        # I create a PoS order
        self.pos_order_pos0 = self.PosOrder.create({
            'company_id': self.company_id,
            'folio_id': "123",
            'pricelist_id': self.partner1.property_product_pricelist.id,
            'partner_id': self.partner1.id,
            'session_id': self.pos_order_session0.id,
            'lines': [(0, 0, {
                'name': "OL/0001",
                'product_id': self.product3.id,
                'price_unit': self.product3.list_price,
                'discount': 0.0,
                'qty': 1.0,
                'tax_ids': [(6, 0, self.product3.taxes_id.ids)],
            }), (0, 0, {
                'name': "OL/0002",
                'product_id': self.product3.id,
                'price_unit': self.product3.list_price,
                'discount': 0.0,
                'qty': 2.0,
                'tax_ids': [(6, 0, self.product3.taxes_id.ids)],
            })]
        })
        context_make_payment = {
            "active_ids": [self.pos_order_pos0.id], "active_id": self.pos_order_pos0.id}
        self.pos_make_payment_1 = self.PosMakePayment.with_context(context_make_payment).create({
            'amount': (242 * 3)  # (450 * 2 + 300 * 3 * 1.05) * 0.95 - 100.0
        })
        self.pos_make_payment_1.with_context(context_make_payment).check()
        # I check that the order is marked as paid
        # self.assertEqual(self.pos_order_pos0.state, 'paid', 'Order should be in paid state.')
        # I generate the journal entries
        # self.pos_order_pos0._create_account_move_line()

