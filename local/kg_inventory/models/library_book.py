# -*- coding: utf-8 -*-

from collections import namedtuple
import json
import time

from itertools import groupby
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from operator import itemgetter


class KGPicking(models.Model):
    _inherit = 'stock.picking.type'



class KGPicking(models.Model):
    _inherit = 'stock.picking'

    location_barcode = fields.Char(
        'barcode location',
    )