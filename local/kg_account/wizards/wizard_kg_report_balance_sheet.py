import copy
import os

from dateutil import parser

from odoo import api,fields,models,_
from odoo.modules import get_module_path
from odoo.exceptions import UserError
from datetime import datetime
import json


VALUE_TYPE_ACTUAL = 'actual'


class WizardKgReportBalanceSheet(models.TransientModel):
    _inherit = "wizard.kg.report.income_statement"
    _name = 'wizard.kg.report.balance_sheet'
    _title = "KG Report - Balance Sheet"

    @api.model
    def _get_account_report(self):
        menu = 'balance sheet'
        reports = self.env['account.financial.report'].search([('name', 'ilike', menu)])
        return reports and reports[0] or False

    account_report_id = fields.Many2one('account.financial.report', string='Account Reports', required=True,
                                        default=_get_account_report)
    is_show_ratio = fields.Boolean(default=False, string="Display Ratio")

    date_filter_type = fields.Selection(
        [('date_single', 'Date'),
         ],
        string='Filter by', required=True,
        default='date_single')

    filter_cmp = fields.Selection(
        [('filter_date', 'Date'), ('filter_same', 'Same Period/Date'), ('filter_last_year', 'Last Year')
         , ('filter_ytd', 'Year to Date')],
        string='Filter by', required=True,
        default='filter_last_year')

    value_type = fields.Selection(
        [(VALUE_TYPE_ACTUAL, 'Actual')], string='Value Type',
        required=True, default=VALUE_TYPE_ACTUAL)

    # enable_filter = fields.Boolean(string='Enable Comparison')
    value_type_cmp = fields.Selection(
        [(VALUE_TYPE_ACTUAL, 'Actual')], string='Compare to Value',
        required=True, default=VALUE_TYPE_ACTUAL)

    @staticmethod
    def _define_report_name():
        return "/kg_account/static/rpt/BalanceSheet.mrt"

    @api.onchange('value_type')
    def value_type_onchange(self):
        self.first_column_set_label = 'CURRENT'

    @api.onchange('value_type_cmp')
    def value_type_cmp_onchange(self):
        self.second_column_set_label = 'COMPARE TO'

    def _build_contexts(self):
        result = {}
        result['state'] = self.target_move
        result['date_from'] = False
        result['date_to'] = self.date_to
        result['value_type'] = self.value_type
        return result

    def _build_comparison_context(self):
        result = {}
        # result['journal_ids'] = False
        result['state'] = self.target_move or ''
        result['date_from'] = False
        result['date_to'] = self.date_to_cmp
        result['value_type'] = self.value_type_cmp
        return result
