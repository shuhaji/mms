import time
from datetime import datetime

import odoo
from odoo import fields
from odoo.tools import float_compare, mute_logger, test_reports
from odoo.tests import common

# @odoo.tests.common.at_install(False)
# @odoo.tests.common.post_install(True)


class TestAccountPeriod(common.TransactionCase):

    def setUp(self):
        super(TestAccountPeriod, self).setUp()
        self.env.user.company_id.hotel_id = 45

    def test_lock_last_month(self):
        result = self.env['account.period'].lock_last_month()
        self.assertTrue(result, "Failed to get execute Acount Period-Lock Last Month")

        # last_month_date = datetime.now().replace(month=datetime.now().month-1)
        # period = self.env['account.period'].search()
