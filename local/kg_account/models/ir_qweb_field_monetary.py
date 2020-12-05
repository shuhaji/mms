# -*- coding: utf-8 -*-
import base64
import re
from collections import OrderedDict
from io import BytesIO
from odoo import api, fields, models, _
from PIL import Image
import babel
from lxml import etree
import math

from odoo.tools import html_escape as escape, posix_to_ldml, safe_eval, float_utils, format_date, pycompat

import logging
_logger = logging.getLogger(__name__)


class KGIrQwebFieldMonetary(models.AbstractModel):
    _inherit = 'ir.qweb.field.monetary'

    # @api.model
    # def value_to_html(self, value, options):
    #     display_currency = options['display_currency']
    #
    #     # custom code
    #     if options.get('template_options', False):
    #             if options.get('template_options', False).get('active_model', False):
    #                 if options.get('template_options', False).get('active_model', False) \
    #                     == 'account.aged.trial.balance':
    #                     display_currency.decimal_places = 0
    #     # end of custom code
    #
    #     # lang.format mandates a sprintf-style format. These formats are non-
    #     # minimal (they have a default fixed precision instead), and
    #     # lang.format will not set one by default. currency.round will not
    #     # provide one either. So we need to generate a precision value
    #     # (integer > 0) from the currency's rounding (a float generally < 1.0).
    #     fmt = "%.{0}f".format(display_currency.decimal_places)
    #
    #     if options.get('from_currency'):
    #         value = options['from_currency'].compute(value, display_currency)
    #
    #     lang = self.user_lang()
    #     formatted_amount = lang.format(fmt, display_currency.round(value),
    #                             grouping=True, monetary=True).replace(r' ', u'\N{NO-BREAK SPACE}').replace(r'-', u'-\N{ZERO WIDTH NO-BREAK SPACE}')
    #
    #     pre = post = u''
    #     if display_currency.position == 'before':
    #         pre = u'{symbol}\N{NO-BREAK SPACE}'.format(symbol=display_currency.symbol or '')
    #
    #         # custom code
    #         if options.get('template_options', False):
    #             if options.get('template_options', False).get('active_model', False):
    #                 if options.get('template_options', False).get('active_model', False) \
    #                     == 'account.aged.trial.balance':
    #                     pre = u'{symbol}\N{NO-BREAK SPACE}'.format(symbol='')
    #         # end of custom code
    #
    #     else:
    #         post = u'\N{NO-BREAK SPACE}{symbol}'.format(symbol=display_currency.symbol or '')
    #
    #     return u'{pre}<span class="oe_currency_value">{0}</span>{post}'.format(formatted_amount, pre=pre, post=post)
