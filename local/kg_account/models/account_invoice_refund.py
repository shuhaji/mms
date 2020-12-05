# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError


class KGAccountInvoiceRefund(models.TransientModel):
    _inherit = 'account.invoice.refund'

    filter_refund_selection = fields.Selection(
        [
            ('modify', 'Modify: create credit note, reconcile and create a new draft invoice'),
        ],
        string='Filter Refund',
        default='modify',
        store=False
    )

    @api.onchange('filter_refund_selection')
    def filter_refund_selection_onchange(self):
        for rec in self:
            rec.filter_refund = rec.filter_refund_selection
