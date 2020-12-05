# -*- coding: utf-8 -*-
##########################################################################
#
#    Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
##########################################################################
from odoo import api, fields, models, _
from odoo import tools
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class VoucherHistory(models.Model):
    _inherit = "voucher.history"

    pos_order_id = fields.Many2one('pos.order', 'Pos Order Id')
    pos_order_line_id = fields.Many2one('pos.order.line', 'Pos OrderLine Id')
