import copy
import os

from dateutil import parser

from odoo import api,fields,models,_
from odoo.modules import get_module_path
from odoo.exceptions import UserError
from datetime import datetime
import json


VALUE_TYPE_ACTUAL = 'actual'


class WizardKgReportCashFlow(models.TransientModel):
    _inherit = "wizard.kg.report.income_statement"
    _name = 'wizard.kg.report.cash_flow'
    _title = "KG Report - Cash Flow"

    is_cash_flow_report = True

    # proses kalkulasi utk report cash flow sebagian besar dilakukan
    #  di dalam wizard_kg_report_income_statement.py

    @api.model
    def _get_account_report(self):
        menu = 'cash flow'
        reports = self.env['account.financial.report'].search([('name', 'ilike', menu)])
        return reports and reports[0] or False

    account_report_id = fields.Many2one('account.financial.report', string='Account Reports', required=True,
                                        default=_get_account_report)
    is_show_ratio = fields.Boolean(default=False, string="Display Ratio")
    filter_cmp = fields.Selection(
        [('filter_date', 'Date'),
         ('filter_same', 'Same Period/Date'),
         ('filter_last_year', 'Last Year')],
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
        return "/kg_account/static/rpt/CashFlow.mrt"

    @api.onchange('value_type')
    def value_type_onchange(self):
        self.first_column_set_label = 'CURRENT'

    @api.onchange('value_type_cmp')
    def value_type_cmp_onchange(self):
        self.second_column_set_label = 'COMPARE TO'
