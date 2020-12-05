import copy
import os

from dateutil import parser
from dateutil.relativedelta import relativedelta

from odoo import api,fields,models,_
from odoo.modules import get_module_path
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import json


VALUE_TYPE_ACTUAL = 'actual'
VALUE_TYPE_BUDGET = 'budget'
VALUE_TYPE_ACTUAL_VS_BUDGET = 'actual_vs_budget'


class WizardKgReportFinancial(models.TransientModel):
    _inherit = 'wizard.kg.report.base'
    _name = 'wizard.kg.report.income_statement'
    _title = "KG Report - Income Statement"

    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 default=lambda self: self.env.user.company_id)

    date_start_fiscal_year = fields.Date(string='fiscal year start at', readonly=True)
    date_end_fiscal_year = fields.Date(string='fiscal year end at', readonly=True)

    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')
    # journal_ids = fields.Many2many('account.journal', string='Journals', required=True,
    #                                default=lambda signerself: self.env['account.journal'].search([]))
    debit_credit = fields.Boolean(
        string='Display Debit/Credit Columns',
        default=False,
        help="This option allows you to get more details about the way your balances are computed. "
             "Because it is space consuming, we do not allow to use it while doing a comparison.")

    @api.model
    def _get_account_report(self):
        menu = 'Income Statement'
        reports = self.env['account.financial.report'].search([('name', 'ilike', menu)])
        return reports and reports[0] or False

    account_report_id = fields.Many2one('account.financial.report', string='Account Reports', required=True,
                                        default=_get_account_report)

    is_show_ratio = fields.Boolean(default=True, string="Display Ratio")
    value_type = fields.Selection(
        [(VALUE_TYPE_ACTUAL, 'Actual'), (VALUE_TYPE_BUDGET, 'Budget'),
         (VALUE_TYPE_ACTUAL_VS_BUDGET, 'Actual,Budget, and Compare'),
         ], string='Value Type',
        required=True, default=VALUE_TYPE_ACTUAL)

    enable_filter = fields.Boolean(string='Enable Comparison')
    value_type_cmp = fields.Selection(
        [(VALUE_TYPE_ACTUAL, 'Actual'), (VALUE_TYPE_BUDGET, 'Budget')], string='Compare to Value',
        required=True, default=VALUE_TYPE_BUDGET)

    date_filter_type = fields.Selection(
        [('date_single', 'Date'),
         ('date_range', 'Date Range'),
         ('period', 'Period (Month-Year)'),
         ('filter_ytd', 'Year to Date'),
         ],
        string='Filter by', required=True,
        default='period')
    period = fields.Date(string='Period', default=fields.Date.today)
    date_from = fields.Date(string='Start Date', default=fields.Date.today)
    date_to = fields.Date(string='End Date', default=fields.Date.today)
    date_from_to_show = fields.Date(
        string='Start Date', readonly=True,
        related='date_from')
    date_to_to_show = fields.Date(
        string='End Date', readonly=True,
        related='date_to')

    filter_cmp = fields.Selection(
        [('filter_date', 'Date Range'),
         ('filter_same', 'Same Period/Date'),
         ('filter_period', 'Period (Month-Year)'),
         ('filter_last_year', 'Last Year'),
         ('filter_ytd', 'Year to Date'),
         ],
        string='Filter by', required=True,
        default='filter_same')
    period_cmp = fields.Date(string='Period', default=fields.Date.today)
    date_from_cmp = fields.Date(string='Start Date', default=fields.Date.today)
    date_to_cmp = fields.Date(string='End Date', default=fields.Date.today)
    date_from_cmp_to_show = fields.Date(
        string='Start Date', readonly=True,
        related='date_from_cmp')
    date_to_cmp_to_show = fields.Date(
        string='End Date', readonly=True,
        related='date_to_cmp')

    first_column_set_label = fields.Char(
        string='First Column Set Label',
        help="This label will be displayed on report to show (for the first column set)")
    second_column_set_label = fields.Char(
        string='Second Column Set Label',
        help="This label will be displayed on report to show (for the third column set)")
    is_show_third_column_set = fields.Boolean(default=False, string="Show Variance")
    third_column_set_label = fields.Char(
        default="VARIANCE",
        string='Third Column Set Label',
        help="This label will be displayed on report to show (for the second column set)")
    is_hide_signer = fields.Boolean(default=False, string="Hide Signer (Authorize By, etc)")
    is_cash_flow_report = False

    # crossovered_budget_id = fields.Many2one(
    #     'crossovered.budget', 'Budget',
    #     required=False)

    @api.multi
    def _define_report_name(self):
        if self.value_type == VALUE_TYPE_ACTUAL_VS_BUDGET:
            return "/kg_account/static/rpt/IncomeStatement6set.mrt"
        else:
            return "/kg_account/static/rpt/IncomeStatement.mrt"

    def get_date_from_report_display(self):
        return self.date_from if self.date_filter_type != 'date_single' else ''

    @api.multi
    def _get_data(self):
        """ get data from database or any other source

        :return: dict or list of dict
        """
        # extract financial report data
        financial_data = self.get_financial_data()
        blank_name = "..........................."
        self.report_has_logo = False  # sample report has logo
        data = {
            "config": {
                "company_name": self.env.user.company_id.name,
                "is_show_ratio": self.is_show_ratio,
                "is_hide_signer": self.is_hide_signer,
                "title": self.account_report_id.name,
                "first_set_params": {
                    "value_type": self.value_type,
                    "title": self.first_column_set_label,
                    "date_from": self.get_date_from_report_display(),
                    "date_to": self.date_to,
                },
                "second_set_params": {
                    "value_type": self.value_type_cmp,
                    "title": self.second_column_set_label,
                    "date_from": self.date_from_cmp,
                    "date_to": self.date_to_cmp,
                    "is_visible": self.enable_filter,
                },
                "third_set_params": {
                    "value_type": "variance",
                    "title": self.third_column_set_label,
                    "is_visible": self.is_show_third_column_set,
                },
                "general_manager": self.env.user.company_id.general_manager or blank_name,
                "authorized_by": blank_name,
                "prepared_by": self.env.user.name or blank_name,
            },
            "data": financial_data
        }
        # return self._sample_data_reg_card()
        return data

    @api.multi
    def get_financial_data(self):
        self.ensure_one()
        account_report = self.env['account.financial.report'].search([('id', '=', self.account_report_id.id)])
        child_reports = account_report._get_children_by_order()

        params = self.build_filter_params()
        if self.value_type == VALUE_TYPE_ACTUAL_VS_BUDGET:
            # report with 6 set of columns
            # result: actual x , actual y, variance x-y, budget x, budget y, variance budget x-y

            # get x data: for the first 3 column set, get actual x vs actual y
            params['used_context']['date_from'] = self.date_from
            params['used_context']['date_to'] = self.date_to
            params['used_context']['value_type'] = VALUE_TYPE_ACTUAL
            params['comparison_context']['date_from'] = self.date_from_cmp
            params['comparison_context']['date_to'] = self.date_to_cmp
            params['comparison_context']['value_type'] = VALUE_TYPE_ACTUAL
            financial_data_selected_period = self.get_account_lines(child_reports, params)

            # get y data: get data for column set 4, 5, and 6 (budget x vs budget y period)
            params_compare = copy.deepcopy(params)
            params_compare['used_context']['date_from'] = self.date_from
            params_compare['used_context']['date_to'] = self.date_to
            params_compare['used_context']['value_type'] = VALUE_TYPE_BUDGET
            params_compare['comparison_context']['date_from'] = self.date_from_cmp
            params_compare['comparison_context']['date_to'] = self.date_to_cmp
            params_compare['comparison_context']['value_type'] = VALUE_TYPE_BUDGET
            financial_data_compare = self.get_account_lines(child_reports, params_compare)
            financial_data = self.combine_data(financial_data_selected_period, financial_data_compare)
        else:
            financial_data = self.get_account_lines(child_reports, params)
        return financial_data

    @api.multi
    def build_filter_params(self):
        params = {}
        # data['ids'] = self.env.context.get('active_ids', [])
        # data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        used_context = self._build_contexts()
        params['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')

        comparison_context = self._build_comparison_context()
        params['comparison_context'] = comparison_context

        return params

    def _build_contexts(self):
        result = {}
        result['state'] = self.target_move
        result['date_from'] = self.date_from if self.date_filter_type != 'date_single' else False
        result['strict_range'] = True if result['date_from'] else False
        result['date_to'] = self.date_to
        result['value_type'] = self.value_type
        result['is_compare'] = False
        fiscal_year = self.company_id.compute_fiscalyear_dates(parser.parse(self.date_to))
        result['date_from_fiscal_year'] = fiscal_year.get('date_from')
        return result

    def _build_comparison_context(self):
        result = {}
        # result['journal_ids'] = False
        result['state'] = self.target_move or ''

        if self.date_filter_type == 'date_single' and self.filter_cmp == 'filter_same':
            result['date_from'] = False
        else:
            result['date_from'] = self.date_from_cmp
        result['strict_range'] = True if result['date_from'] else False

        result['date_from'] = self.date_from_cmp
        result['date_to'] = self.date_to_cmp
        result['value_type'] = self.value_type_cmp
        result['is_compare'] = True
        fiscal_year = self.company_id.compute_fiscalyear_dates(parser.parse(self.date_to_cmp))
        result['date_from_fiscal_year'] = fiscal_year.get('date_from')
        return result

    def get_account_lines(self, child_reports, data):
        lines = []
        value_type = data.get('used_context').get('value_type')
        value_type_cmp = data.get('comparison_context').get('value_type')
        all_result = dict()
        res, all_result = self.with_context(data.get('used_context'))._compute_report_layout_balance(
            child_reports, all_result)
        if self.enable_filter:
            all_result = dict()
            comparison_res, all_result = self.with_context(
                data.get('comparison_context'))._compute_report_layout_balance(child_reports, all_result)
            for report_id, value in comparison_res.items():
                res[report_id]['comp_bal'] = value['balance']
                res[report_id]['comp_budget'] = value['budget']
                report_acc = res[report_id].get('account')
                if report_acc:
                    for account_id, val in comparison_res[report_id].get('account').items():
                        report_acc[account_id]['comp_bal'] = val.get('balance', 0)
                        report_acc[account_id]['comp_budget'] = val.get('budget', 0)

        divisor_total_first_set = 0
        divisor_total_second_set = 0
        for report in child_reports:
            if report.is_total_income:
                # GET DIVISOR RATIO
                if value_type == VALUE_TYPE_BUDGET:
                    divisor_total_first_set = abs(res[report.id].get('budget', 0))
                else:
                    divisor_total_first_set = res[report.id]['balance'] * report.sign

                if value_type_cmp == VALUE_TYPE_BUDGET:
                    divisor_total_second_set = abs(res[report.id].get('comp_budget', 0))
                else:
                    divisor_total_second_set = res[report.id].get('comp_bal', 0) * report.sign

        level = 0
        subtotal_vals = {}
        prev_vals = {"level": -1}
        for report in child_reports:
            balance = res[report.id]['balance'] * report.sign
            level = report.level
            if level <= prev_vals.get('level', -1111):
                # check subtotal from previous level! if exists -> add lines sub total before current row
                self._add_sub_total_row(
                    current_level=level, prev_level=prev_vals.get('level', -1111),
                    subtotal_vals=subtotal_vals, lines=lines)

            vals = {
                'report_id': report.id,
                'type': 'report',
                'code': "{seq}".format(seq=report.sequence),
                'name': report.name,
                'balance': balance,
                'level': level,  # was:  bool(report.style_overwrite) and report.style_overwrite or report.level
                'account_type': report.type or False,  # used to underline the financial report balances
                'report_name': report.name,  # 1st group
                'parent_name': report.parent_info,  # 2nd group
                'grand_parent_name': report.grand_parent_info,  # 3rd group
                'parent_id': report.parent_id.id if report.parent_id else None,
                'is_show_at_group_header': report.is_show_at_group_header,  # show row data on report
                'is_show_total': not report.is_show_total_at_bottom,
                'is_show_border_top': report.is_show_border_top,
                'is_show_border_bottom': report.is_show_border_bottom,
                'style_overwrite': report.style_overwrite if report.style_overwrite else 4,
                # (0, 'Automatic formatting'),
                # (1, 'Main Title 1 (bold, underlined)'),
                # (2, 'Title 2 (bold)'),
                # (3, 'Title 3 (bold, smaller)'),
                # (4, 'Normal Text'),
                # (5, 'Italic Text (smaller)'),
                # (6, 'Smallest Text'),
            }
            if self.debit_credit:
                vals['debit'] = res[report.id]['debit']
                vals['credit'] = res[report.id]['credit']

            balance_cmp = res[report.id].get('comp_bal', 0) * report.sign
            budget = abs(res[report.id].get('budget', 0))
            budget_cmp = abs(res[report.id].get('comp_budget', 0))

            vals['enable_compare'] = self.enable_filter
            self.define_column_set_values(
                vals, balance, balance_cmp, budget, budget_cmp, divisor_total_first_set,
                divisor_total_second_set, value_type, value_type_cmp)

            lines.append(vals)
            prev_vals = copy.deepcopy(vals)

            copy_to_subtotal_vals = None
            if report.is_show_total_at_bottom:
                # add sub total
                copy_to_subtotal_vals = copy.deepcopy(vals)
                copy_to_subtotal_vals['name'] = report.label_total_bottom or ''
                copy_to_subtotal_vals['is_show_at_group_header'] = True  # show row data on report
                copy_to_subtotal_vals['type'] = 'total'
                copy_to_subtotal_vals['is_show_total'] = True

            if report.display_detail != 'no_detail' and \
                    report.type in ['accounts', 'account_type', 'account_group']:
                # display the details of the financial report
                lines, sub_lines = self.add_account_detail_lines(
                    data, lines, report, res,
                    divisor_total_first_set, divisor_total_second_set, value_type, value_type_cmp)

                if copy_to_subtotal_vals and sub_lines and report.is_show_total_at_bottom:
                    lines.append(copy_to_subtotal_vals)
            else:
                if copy_to_subtotal_vals and report.is_show_total_at_bottom:
                    subtotal_vals[level] = copy_to_subtotal_vals

        if subtotal_vals:
            # loop and display the remaining total if any
            self._add_sub_total_row(
                current_level=0, prev_level=level, subtotal_vals=subtotal_vals, lines=lines)

        return lines

    def _add_sub_total_row(self, current_level, prev_level, subtotal_vals, lines):
        key_levels = list(range(current_level, prev_level + 1))[::-1]  # reverse, from higher level value to zero
        for k in key_levels:
            subtotal_row = subtotal_vals.pop(k, None)  # get and delete from queue
            if subtotal_row:
                lines.append(subtotal_row)

    def define_column_set_values(self, vals, balance, balance_cmp, budget, budget_cmp, divisor_total_first_set,
                                 divisor_total_second_set, value_type, value_type_cmp):
        if value_type == VALUE_TYPE_BUDGET:
            vals['first_set_value'] = budget
            vals['first_set_ratio'] = round((budget * 100) / divisor_total_first_set, 2) \
                if divisor_total_first_set else 0
        else:
            vals['first_set_value'] = balance  # actual
            vals['first_set_ratio'] = round((balance * 100) / divisor_total_first_set, 2) \
                if divisor_total_first_set else 0

        if value_type_cmp == VALUE_TYPE_BUDGET:
            vals['second_set_value'] = budget_cmp
            vals['second_set_ratio'] = round((budget_cmp * 100) / divisor_total_second_set, 2) \
                if divisor_total_second_set else 0
        else:
            vals['second_set_value'] = balance_cmp  # actual
            vals['second_set_ratio'] = round((balance_cmp * 100) / divisor_total_second_set, 2) \
                if divisor_total_second_set else 0

        vals['third_set_value'] = vals['first_set_value'] - vals['second_set_value']
        divisor_for_variance = vals['second_set_value']
        vals['third_set_ratio'] = round((vals['third_set_value'] * 100) / divisor_for_variance, 2) \
            if divisor_for_variance else 0

    def _compute_account_balance(self, accounts, reverse_balance_value=1):
        """ compute the balance, debit and credit for the provided accounts
        """
        mapping = {
            'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) * {reverse_balance_value}"
                       "as balance".format(reverse_balance_value=reverse_balance_value),
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
            'budget': "0 as budget",
        }

        res = {}
        for account in accounts:
            res[account.id] = dict.fromkeys(mapping, 0.0)
            res[account.id]['budget'] = 0

        # utk query, data filter disimpan dalam variable context (self._context)
        context_params = dict(self._context or {})

        if accounts:
            if context_params.get('value_type') == VALUE_TYPE_BUDGET:
                # request = "with z_kg_account_financial_summary as (" \
                #         + request \
                #         + ") " \
                request = " select cbl.account_id as id, 0 as balance, 0 as debit, 0 as credit, " \
                          " COALESCE(SUM(cbl.planned_amount), 0) as budget" \
                          " from crossovered_budget_lines cbl " \
                          " WHERE cbl.account_id IN %s " \
                          "   and cbl.date_from >= %s and cbl.date_to <= %s" \
                          " group by cbl.account_id "

                params = (tuple(accounts._ids),) + (
                    context_params.get('date_from', self.date_from),
                    context_params.get('date_to', self.date_to))
            else:
                # utk query, data filter disimpan dalam variable context (self._context)
                tables, where_clause, where_params = self.env['account.move.line']._query_get()
                tables = tables.replace('"', '') if tables else "account_move_line"
                wheres = [""]
                if where_clause.strip():
                    wheres.append(where_clause.strip())
                filters = " AND ".join(wheres)
                request = "SELECT account_id as id, " + ', '.join(mapping.values()) + \
                          " FROM " + tables + \
                          " WHERE account_id IN %s " \
                          + filters + \
                          " GROUP BY account_id "
                params = (tuple(accounts._ids),) + tuple(where_params)

            self.env.cr.execute(request, params)
            result = self.env.cr.dictfetchall()
            for row in result:
                res[row['id']] = row
        return res

    def _compute_cash_flow_initial_balance(self):
        # utk query, data filter disimpan dalam variable context (self._context)
        context_params = dict(self._context or {})
        original_date_from = context_params.get('date_from', self.date_from)
        # original_date_to = context_params.get('date_to', self.date_to)
        date_val = parser.parse(original_date_from)
        date_to = date_val + relativedelta(days=-1)

        # context_params['date_from'] = context_params['date_from_fiscal_year']
        context_params['date_from'] = None
        context_params['date_to'] = date_to
        # get sum account move line for account type = 3 (bank and cash)
        #   from the start of fiscal year until date from/start
        # TODO: improve: hitung beginning balance dari table/view beginning balance
        accounts = self.env['account.account'].search([('user_type_id', '=', 3), ('company_id', '=', self.company_id.id)])
        result = self.with_context(context_params)._compute_account_balance(accounts)
        return result

    @staticmethod
    def field_names():
        return ['credit', 'debit', 'balance', 'budget']

    def _compute_report_layout_balance(self, reports, all_result=None):
        '''returns a dictionary with key=the ID of a record and value=the credit, debit and balance amount
           computed for this record. If the record is of type :
               'accounts' : it's the sum of the linked accounts
               'account_type' : it's the sum of leaf accoutns with such an account_type
               'account_report' : it's the amount of the related report
               'sum' : it's the sum of the children of this record (aka a 'view' record)'''
        res = {}
        if all_result is None:
            all_result = dict()
        fields = self.field_names()

        for report in reports:
            if report.id in res:
                continue
            elif report.id in all_result:
                res[report.id] = all_result[report.id]
                continue
            res[report.id] = dict((fn, 0.0) for fn in fields)

            if self.is_cash_flow_report and report.is_cf_init_balance:
                res[report.id]['account'] = self._compute_cash_flow_initial_balance()
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field, 0)
            elif report.type == 'accounts':
                # it's the sum of the linked accounts
                res[report.id]['account'] = self._compute_account_balance(report.account_ids, report.reverse_balance_value)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field, 0)
            elif report.type == 'account_type':
                # it's the sum the leaf accounts with such an account type
                accounts = self.env['account.account'].search([('user_type_id', 'in', report.account_type_ids.ids)])
                res[report.id]['account'] = self._compute_account_balance(accounts, report.reverse_balance_value)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field, 0)
            elif report.type == 'account_group':
                # it's the sum the leaf accounts with such an account group
                if self.is_cash_flow_report:
                    # for report cash flow, filter account by cash flow group
                    accounts = self.env['account.account'].search([
                        ('cash_flow_group_id', 'in', report.account_group_ids.ids)])
                else:
                    # non cash flow report
                    accounts = self.env['account.account'].search([('group_id', 'in', report.account_group_ids.ids)])
                res[report.id]['account'] = self._compute_account_balance(accounts, report.reverse_balance_value)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field, 0)
            elif report.type == 'account_report' and report.account_report_id:
                # it's the amount of the linked report
                if res.get(report.account_report_id):
                    # check if already calculated in this loop, get from existing values!
                    res2 = copy.deepcopy(res.get(report.account_report_id))
                elif all_result.get(report.account_report_id):
                    # check if already calculated from the previous loop, get from existing values!
                    res2 = copy.deepcopy(all_result.get(report.account_report_id))
                else:
                    res2, all_result = self._compute_report_layout_balance(report.account_report_id, all_result=all_result)

                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value.get(field, 0) * report.reverse_balance_value
            elif report.type == 'sum':
                # it's the sum of the children of this account.report
                res2, all_result = self._compute_report_layout_balance(report.children_ids, all_result=all_result)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value.get(field, 0) * report.reverse_balance_value

            # update list of all previous result (to prevent recalculation/re-processing data)
            all_result[report.id] = res.get(report.id)
        return res, all_result

    def add_account_detail_lines(self, data, lines, report, res,
                                 divisor_total_first_set, divisor_total_second_set, value_type, value_type_cmp):
        sub_lines = []
        if res[report.id].get('account'):
            for account_id, value in res[report.id]['account'].items():
                # if there are accounts to display, we add them to the lines with a level equals to their level in
                # the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                # financial reports for Assets, liabilities...)
                flag = False
                account = self.env['account.account'].browse(account_id)
                balance = value['balance'] * report.sign or 0.0
                vals = {
                    'code': "{seq}-{code}".format(seq=report.sequence, code=account.code),
                    'name': account.name,
                    'balance': value['balance'] * report.sign or 0.0,
                    'type': 'account',
                    'level': report.display_detail == 'detail_with_hierarchy' and 4,
                    'account_type': account.internal_type,
                    'report_name': report.name,  # 1st group
                    'parent_name': report.parent_info,  # 2nd group
                    'grand_parent_name': report.grand_parent_info,  # 3hd group
                    'is_show_at_group_header': True,  # show row data on report
                    'is_show_total': True,
                    'parent_id': report.parent_id.id,
                }
                if self.debit_credit:
                    vals['debit'] = value['debit']
                    vals['credit'] = value['credit']
                    if not account.company_id.currency_id.is_zero(
                            vals['debit']) or not account.company_id.currency_id.is_zero(vals['credit']):
                        flag = True

                balance_cmp = value.get('comp_bal', 0) * report.sign
                budget = abs(value.get('budget', 0))
                budget_cmp = abs(value.get('comp_budget', 0))

                amount_check = budget if value_type == VALUE_TYPE_BUDGET else balance
                if not account.company_id.currency_id.is_zero(amount_check):
                    flag = True
                if self.enable_filter:
                    # vals['balance_cmp'] = value['comp_bal'] * report.sign
                    amount_check = budget_cmp if value_type_cmp == VALUE_TYPE_BUDGET else balance_cmp
                    if not account.company_id.currency_id.is_zero(amount_check):
                        flag = True
                if flag:
                    vals['enable_compare'] = self.enable_filter
                    self.define_column_set_values(
                        vals, balance, balance_cmp, budget, budget_cmp, divisor_total_first_set,
                        divisor_total_second_set, value_type, value_type_cmp)

                    sub_lines.append(vals)
            lines += sorted(sub_lines, key=lambda sub_line: sub_line['code'])
        return lines, sub_lines

    @api.onchange('enable_filter')
    def enable_filter_onchange(self):
        self.is_show_third_column_set = self.enable_filter

    @api.onchange('value_type')
    def value_type_onchange(self):
        if self.value_type == VALUE_TYPE_ACTUAL_VS_BUDGET:
            self.first_column_set_label = "ACTUAL"
            self.enable_filter = True
            self.filter_cmp = 'filter_last_year'
            self.value_type_cmp = VALUE_TYPE_ACTUAL
        else:
            self.first_column_set_label = self.value_type.upper() if self.value_type else ''

    @api.model
    @api.onchange('value_type_cmp')
    def value_type_cmp_onchange(self):
        self.second_column_set_label = self.value_type_cmp.upper() if self.value_type_cmp else ''

    @api.model
    @api.onchange('date_filter_type', 'period')
    def filter_date_onchange(self):
        date_val = parser.parse(self.date_from) if self.date_from else False
        if self.date_filter_type == 'period':
            self.date_from, self.date_to = self.set_period(self.period)
        elif self.date_filter_type == 'filter_ytd':
            self.date_from = date_val.replace(day=1, month=1) if date_val else False
            self.date_to = fields.Date.today()

    @api.model
    @api.onchange('filter_cmp', 'date_to', 'period_cmp')
    def filter_date_compare_onchange(self):
        date_val = parser.parse(self.date_from) if self.date_from else False
        if self.filter_cmp == 'filter_last_year':
            self.date_from_cmp = date_val.replace(year=date_val.year - 1) if date_val else False
            if self.date_to:
                date_val_to = parser.parse(self.date_to)
                self.date_to_cmp = date_val_to.replace(year=date_val.year - 1) if date_val else False
            else:
                self.date_to_cmp = False
        elif self.filter_cmp == 'filter_same':
            self.date_from_cmp = self.date_from
            self.date_to_cmp = self.date_to
        elif self.filter_cmp == 'filter_ytd':
            self.date_from_cmp = date_val.replace(day=1, month=1) if date_val else False
            self.date_to_cmp = self.date_to
        elif self.filter_cmp == 'filter_period':
            self.date_from_cmp, self.date_to_cmp = self.set_period(self.period_cmp)

    @api.onchange('date_to')
    def date_to_onchange(self):
        if self.date_to:
            fiscal_year = self.company_id.compute_fiscalyear_dates(parser.parse(self.date_to))
            self.date_start_fiscal_year = fiscal_year.get('date_from')
            self.date_end_fiscal_year = fiscal_year.get('date_to')
            self.filter_date_compare_onchange()

    @api.model
    def set_period(self, period):
        if period:
            date_val = parser.parse(period)
            date_from = date_val.replace(day=1) if date_val else False
            date_to = date_from + relativedelta(months=1, days=-1) if date_from else False
            return date_from, date_to
        else:
            return False, False

    @api.multi
    def combine_data(self, financial_data_selected_period, financial_data_compare):
        for data in financial_data_selected_period:
            for compare_data in financial_data_compare:
                if compare_data.get('report_id') == data.get('report_id') and \
                        compare_data.get('name') == data.get('name') and \
                        compare_data.get('type') == data.get('type'):
                    data['4_set_value'] = compare_data.get('first_set_value', 0)
                    data['4_set_ratio'] = compare_data.get('first_set_ratio', 0)
                    data['5_set_value'] = compare_data.get('second_set_value', 0)
                    data['5_set_ratio'] = compare_data.get('second_set_ratio', 0)
                    data['6_set_value'] = compare_data.get('third_set_value', 0)
                    data['6_set_ratio'] = compare_data.get('third_set_ratio', 0)
        return financial_data_selected_period
