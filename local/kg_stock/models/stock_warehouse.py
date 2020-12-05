from collections import namedtuple
from datetime import datetime
from dateutil import relativedelta

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

import logging


_logger = logging.getLogger(__name__)


class Warehouse(models.Model):
    _inherit = "stock.warehouse"

    @api.model
    def create(self, values):
        stock_location_id = self.env.ref('stock.stock_location_locations').id
        cr = self._cr
        cr.execute("SELECT parent_left FROM stock_location WHERE id=%s", (stock_location_id,))
        parent_left = cr.fetchone()
        if parent_left and parent_left[0] is None:
            self.env['stock.location']._parent_store_compute()

        result = super(Warehouse, self).create(values)
        return result
