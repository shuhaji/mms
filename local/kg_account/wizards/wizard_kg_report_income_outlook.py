import copy
from dateutil import parser

from odoo import api, fields, models, _
from odoo.addons.kg_account.wizards.wizard_kg_report_income_statement import VALUE_TYPE_ACTUAL, VALUE_TYPE_BUDGET
from datetime import datetime, timedelta


VALUE_TYPE_OUTLOOK = 'outlook'


class WizardKgReportFinancialIncomeStatementOutloo(models.TransientModel):
    _inherit = 'wizard.kg.report.income_statement'
    _name = 'wizard.kg.report.income_statement_outlook'
    _title = "KG Report - Outlook Income Statement"

    value_type = fields.Selection(
        [(VALUE_TYPE_OUTLOOK, 'Outlook'),
         ], string='Value Type',
        required=True, default=VALUE_TYPE_OUTLOOK)
    date_filter_type = fields.Selection(
        [('period', 'Period (Month-Year)'),
         ],
        string='Filter by', required=True,
        default='period')
    enable_filter = fields.Boolean(string='Enable Comparison', default=True)
    is_show_ratio = fields.Boolean(default=True, string="Display Ratio")
    is_cash_flow_report = False

    @api.multi
    def _define_report_name(self):
        return "/kg_account/static/rpt/IncomeOutlook.mrt"

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
                "is_show_ratio": True,
                "is_hide_signer": self.is_hide_signer,
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
                    "is_visible": True,
                },
                "third_set_params": {
                    "value_type": "",
                    "title": "",
                    "is_visible": True,
                },
                "accounting_manager": self.env.user.company_id.accounting_manager or blank_name,
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
        financial_data = self.get_account_lines(child_reports, params)
        return financial_data

    def get_date_from_report_display(self):
        date_to = parser.parse(self.date_to) if not isinstance(self.date_to, datetime) else self.date_to
        return self.get_from_date(date_to, target_from_month=1)

    @staticmethod
    def get_from_date(end_date, target_from_month):
        return end_date.replace(month=target_from_month, day=1).isoformat().split('T')[0]

    def _build_contexts(self):
        result = dict()
        result['state'] = self.target_move
        result['strict_range'] = True
        date_to = parser.parse(self.date_to) if not isinstance(self.date_to, datetime) else self.date_to
        result['date_from'] = self.get_from_date(date_to, target_from_month=1)
        result['date_to'] = self.date_to
        result['value_type'] = VALUE_TYPE_ACTUAL
        return result

    def _build_comparison_context(self):
        result = dict()
        # result['journal_ids'] = False
        result['state'] = self.target_move or ''
        date_to = parser.parse(self.date_to) if not isinstance(self.date_to, datetime) else self.date_to
        result['date_from'] = date_to + timedelta(days=1)
        jan_date = parser.parse(self.get_from_date(date_to, target_from_month=1))
        jan_date_next_year = jan_date.replace(year=jan_date.year+1)
        end_of_year = jan_date_next_year - timedelta(days=1)
        result['date_to'] = end_of_year
        result['value_type'] = VALUE_TYPE_BUDGET
        return result

    @staticmethod
    def fill_amount_budgets(budget_months, report_row, data_value):
        for month in budget_months:
            amount_col = 'amount_{month}'.format(month=month)
            report_row[amount_col] = data_value.get(amount_col, 0)
        return report_row

    def get_account_lines(self, child_reports, data):
        lines = []
        date_to = parser.parse(self.date_to) if not isinstance(self.date_to, datetime) else self.date_to
        all_months = list(range(1, 13))
        actual_months = list(range(1, date_to.month + 1))
        budget_months = list(range(date_to.month + 1, 13))
        all_result = dict()
        res, all_result = self.with_context(data.get('used_context'))._compute_report_layout_balance(
            child_reports, all_result)
        if self.enable_filter:
            all_result = dict()
            comparison_res, all_result = self.with_context(
                data.get('comparison_context'))._compute_report_layout_balance(child_reports, all_result)
            for report_id, value in comparison_res.items():
                res[report_id] = self.fill_amount_budgets(budget_months, res[report_id], value)
                # res[report_id]['comp_budget'] = value['budget']
                report_acc = res[report_id].get('account')
                if report_acc:
                    for account_id, val in comparison_res[report_id].get('account').items():
                        if not report_acc.get(account_id, False):
                            report_acc[account_id] = {"id": account_id}
                        report_acc[account_id] = self.fill_amount_budgets(budget_months, report_acc[account_id], val)
                        # report_acc[account_id]['comp_budget'] = val.get('budget', 0)

        ratio_divisor = dict()
        for report in child_reports:
            if report.is_total_income:
                # GET DIVISOR FOR RATIO
                for month in all_months:
                    ratio_divisor[month] = abs(res[report.id].get('amount_{month}'.format(month=month), 0))

        level = 0
        subtotal_vals = {}
        prev_vals = {"level": -1}
        for report in child_reports:
            balance = res[report.id].get('balance', 0) * report.sign
            level = report.level
            if level <= prev_vals.get('level', -1111):
                # check subtotal from previous level! if exists -> add lines sub total before current row
                self._add_sub_total_row(
                    current_level=level, prev_level=prev_vals.get('level', -1111),
                    subtotal_vals=subtotal_vals, lines=lines)

            vals = {
                'report_id': report.id,
                'type': 'report',
                'name': report.name,
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
                'is_total_income': report.is_total_income,
                'style_overwrite': report.style_overwrite if report.style_overwrite else 4,
                # (0, 'Automatic formatting'),
                # (1, 'Main Title 1 (bold, underlined)'),
                # (2, 'Title 2 (bold)'),
                # (3, 'Title 3 (bold, smaller)'),
                # (4, 'Normal Text'),
                # (5, 'Italic Text (smaller)'),
                # (6, 'Smallest Text'),
            }
            self.define_amount_column_values(report, res, vals, ratio_divisor, all_months, actual_months, budget_months)

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
                    ratio_divisor, all_months, actual_months, budget_months)

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

    @staticmethod
    def define_amount_column_values(report, res, vals, ratio_divisor, all_months, actual_months, budget_months):
        for month in actual_months:
            amount_col = 'amount_{month}'.format(month=month)
            vals[amount_col] = res[report.id].get(amount_col, 0) * report.sign
        for month in budget_months:
            amount_col = 'amount_{month}'.format(month=month)
            vals[amount_col] = abs(res[report.id].get(amount_col, 0))
        for month in all_months:
            # calculate ratio for current row data
            amount_col = 'amount_{month}'.format(month=month)
            amount_ratio_col = 'ratio_{month}'.format(month=month)
            vals[amount_ratio_col] = (vals[amount_col] * 100) / ratio_divisor[month] if ratio_divisor[month] != 0 else 0

    def _compute_account_balance(self, accounts, reverse_balance_value=1):
        """ compute the balance, debit and credit for the provided accounts
        """
        mapping = dict()
        months = list(range(1, 13))
        res = dict()
        context_params = dict(self._context or {})
        if accounts:
            if context_params.get('value_type') == VALUE_TYPE_BUDGET:
                for month_no in months:
                    mapping['amount' + str(month_no)] = \
                        "sum(CASE WHEN EXTRACT(MONTH FROM cbl.date_to) = {month} " \
                        "then COALESCE(cbl.planned_amount, 0) else 0 end) * {reverse_balance_value} as amount_{month}".format(
                            reverse_balance_value=reverse_balance_value, month=month_no
                        )
                request = "  select cbl.account_id as id, " \
                          + ', '.join(mapping.values()) + \
                          " from crossovered_budget_lines cbl " \
                          " WHERE cbl.account_id IN %s " \
                          "   and cbl.date_from >= %s and cbl.date_to <= %s" \
                          " group by cbl.account_id"
                params = (tuple(accounts._ids),) + (
                    context_params.get('date_from', self.date_from),
                    context_params.get('date_to', self.date_to))
            else:
                for month_no in months:
                    mapping['amount' + str(month_no)] = \
                        "sum(CASE WHEN EXTRACT(MONTH FROM account_move_line.date) = {month} " \
                        "then COALESCE(debit,0) - COALESCE(credit, 0) else 0 end)* {reverse_balance_value} " \
                        "as amount_{month}".format(reverse_balance_value=reverse_balance_value, month=month_no
                        )

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
                          " GROUP BY account_id"
                params = (tuple(accounts._ids),) + tuple(where_params)

            self.env.cr.execute(request, params)
            result = self.env.cr.dictfetchall()
            for row in result:
                res[row['id']] = row
        return res

    @staticmethod
    def field_names():
        return ['amount_1', 'amount_2', 'amount_3', 'amount_4', 'amount_5', 'amount_6',
                'amount_7', 'amount_8', 'amount_9', 'amount_10', 'amount_11', 'amount_12']

    def add_account_detail_lines(self, data, lines, report, res,
                                 ratio_divisor, all_months, actual_months, budget_months):
        sub_lines = []
        if res[report.id].get('account'):
            for account_id, value in res[report.id]['account'].items():
                # if there are accounts to display, we add them to the lines with a level equals to their level in
                # the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                # financial reports for Assets, liabilities...)
                flag = False
                account = self.env['account.account'].browse(account_id)
                vals = dict({
                    # 'name': account.code + ' ' + account.name,
                    'name': account.name,
                    'type': 'account',
                    'level': report.display_detail == 'detail_with_hierarchy' and 4,
                    'account_type': account.internal_type,
                    'report_name': report.name,  # 1st group
                    'parent_name': report.parent_info,  # 2nd group
                    'grand_parent_name': report.grand_parent_info,  # 3hd group
                    'is_show_at_group_header': True,  # show row data on report
                    'is_show_total': True,
                    'is_total_income': False,
                    'parent_id': report.parent_id.id,
                })

                vals['enable_compare'] = self.enable_filter
                self.define_amount_column_values(report, res, vals, ratio_divisor, all_months, actual_months,
                                                 budget_months)

                sub_lines.append(vals)
            lines += sorted(sub_lines, key=lambda sub_line: sub_line['name'])
        return lines, sub_lines
