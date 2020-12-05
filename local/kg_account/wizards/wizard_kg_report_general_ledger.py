import os

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.modules import get_module_path
from datetime import datetime
import json


class WizardGeneralLedger(models.TransientModel):
    _inherit = 'wizard.kg.report.base'
    _name = 'wizard.kg.report.general.ledger'
    _title = "KG Report - General Ledger"

    sortby = fields.Selection([('sort_date', 'Account Code & Date'), ('sort_journal_partner', 'Journal & Partner')], string='Sort By',
                              required=True, default='sort_date')
    journal_ids = fields.Many2many('account.journal', string='Journals'
                                   # default=lambda self: self.env['account.journal'].search([])
                                   )
    # journal_ids = fields.Many2many('account.journal', 'account_report_general_ledger_journal_rel', 'account_id',
    #                                'journal_id', string='Journals',
    #                                required=True, default=lambda self: self.env['account.journal'].search([]))
    display_account = fields.Selection([('all', 'All'), ('movement', 'With Movements'),
                                        ('not_zero', 'With Balance Is Not Equal To 0'), ],
                                       string='Display Accounts', required=True, default='not_zero')
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')
    report_type = fields.Selection([('sum', 'Summary'), ('det', 'Details'), ], 'Report Type',
                                   required=True, default='det')

    @api.multi
    def _get_data(self):
        """ get data from database or any other source

        :return: dict or list of dict
        """
        # return {
        #     "test": "abc", "test2": 123
        # }
        # return [
        #     {"test": "abc", "test2": 123},
        #     {"test": "cde", "test2": 124}
        # ]
        # multi key data:
        # return {
        #     "companyInfo": {"name": "abc", "address": "alamat mana saja"},
        #     "reportData": [
        #         {"test": "abc", "test2": 123},
        #         {"test": "cde", "test2": 124}
        #     ]
        # }
        self.report_has_logo = True  # sample report has logo
        codes, current_company = self.get_param()

        data, grand_total = self.get_report_values(current_company)

        return {
            "grand_total": grand_total,
            "data1": data,
        }

    def get_report_values(self, current_company=None):

        cr = self.env.cr

        sql_sort, where_journal_id, where_date, where_state, where_display, \
            having_display, init_date, init_balance = self.query_get_clause()

        if self.report_type == 'sum':
            sql_sum = "SUM"
            sql_select_detail = ", l.date, j.code as journal_code"
            sql_select_display = ", zl.row_no, zl.date AS ldate, zl.journal_code AS lcode"
            sql_select_grand_total = ", -99 row_no, '1945-01-01' as date, ' ' as lcode"
            sql_group_by_detail = " GROUP BY acc.id, l.date, j.code "
        else:
            sql_sum = ""
            sql_select_detail = """,l.id, l.date, l.currency_id, l.move_id, l.ref, l.name as name
                    , m.name as move_name
                    , j.code as journal_code, p.name as partner_name"""
            sql_select_display = """,zl.row_no, zl.date AS ldate, zl.journal_code AS lcode 
                    , zl.currency_id, zl.id AS lid, zl.ref AS lref, zl.name AS lname                  
                    , zl.move_name, zl.partner_name"""
            sql_select_grand_total = """, -99 row_no, '1945-01-01' as date, ' ' as lcode
                    , -1 currency_id, -99 AS lid, ' ' AS lref, ' ' AS lname                  
                    , ' ' move_name, ' ' partner_name
            """
            sql_group_by_detail = ""

        query = """
            WITH 
                z_kg_gl_beg_balance AS (
                    SELECT l.company_id, l.account_id AS account_id, 
                        COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS beg_balance, 
                        COALESCE(SUM(l.debit),0) as init_debit, COALESCE(SUM(l.credit), 0) as init_credit
                    FROM account_move_line l
                        LEFT JOIN account_move m ON (l.move_id=m.id)                         
                    WHERE l.date < '{date_from}'
                        AND l.company_id = {company_id} """ \
                        + where_state + where_journal_id + """                         
                    GROUP BY l.company_id, l.account_id
                ),                
                z_kg_gl_move_line as (
                    select acc.company_id, acc.id as account_id,
                        row_number() over (
                            order by {sql_sort}
                        ) as row_no,                        
                        """ + sql_sum + """(COALESCE(l.debit,0)) as debit,
                        """ + sql_sum + """(COALESCE(l.credit, 0)) as credit,
                        """ + sql_sum + """(COALESCE(l.debit,0) - COALESCE(l.credit, 0)) AS balance
                        """ + sql_select_detail + """
                    FROM  account_account acc
                    left join account_move_line l on (l.account_id = acc.id)  
                    left JOIN account_move m ON (l.move_id=m.id)                    
                    LEFT JOIN account_journal j ON (l.journal_id=j.id)  
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)
                    where l.company_id = {company_id} """ \
                        + where_date + where_state + where_journal_id + \
                sql_group_by_detail + \
            """ Order by {sql_sort}
                ),
                z_kg_gl_sub_total_per_account as (
                    select company_id, account_id AS account_id,
                        sum(debit) as debit_per_account,
                        sum(credit) as credit_per_account,
                        sum(balance) as balance_per_account
                    from z_kg_gl_move_line
                    group by company_id, account_id
                ),
                z_kg_gl_grand_total as (
                    select zl.company_id, '-99999' as code, -99999 row_no, -9999 as account_id,
                        (select sum(beg_balance) from z_kg_gl_beg_balance) as beg_balance
                        , sum(debit) as credit
                        , sum(credit) as debit
                    from z_kg_gl_move_line zl
                    group by zl.company_id
                )
            (
            SELECT acc.company_id, acc.id AS account_id, acc."name" as acc_name, acc.code as acc_code, 
                COALESCE(z.beg_balance,0) AS beg_balance, 
                COALESCE(z.init_debit,0) AS init_debit, 
                COALESCE(z.init_credit,0) AS init_credit, 
                COALESCE(zl.debit,0) AS debit, 
                COALESCE(zl.credit,0) AS credit, 
                COALESCE(zl.balance,0) as balance,
                COALESCE(z.beg_balance,0) + (sum(COALESCE(zl.balance,0)) over (
                        partition by acc.company_id, acc.code order by acc.company_id, acc.code, zl.row_no
                    )) as running_total_balance,
                COALESCE(zst.debit_per_account, 0) as debit_per_account,
                COALESCE(zst.credit_per_account, 0) as credit_per_account,
                COALESCE(z.beg_balance,0) + COALESCE(zst.balance_per_account, 0) AS end_balance
                """ + sql_select_display + """
            FROM  account_account acc
            LEFT JOIN z_kg_gl_beg_balance z on (z.account_id = acc.id)
            left join z_kg_gl_move_line zl on (zl.account_id = acc.id)   
            left join z_kg_gl_sub_total_per_account zst on zst.account_id = acc.id  
            WHERE acc.company_id = {company_id} """ \
                + where_display + """ 
            ORDER BY acc.company_id, acc.code, zl.row_no
            ) UNION (
            -- penting, jumlah kolom di select ini harus sama dg jlh kolom select di atas!
            SELECT zl.company_id, zl.account_id, 'GRAND TOTAL' as acc_name, ' ' as acc_code,
                zl.beg_balance, 
                0 AS init_debit, 
                0 AS init_credit, 
                COALESCE(zl.debit,0) AS debit, 
                COALESCE(zl.credit,0) AS credit, 
                COALESCE(zl.debit,0) - COALESCE(zl.credit,0) as balance,
                0 as running_total_balance,
                0 as debit_per_account,
                0 as credit_per_account,
                COALESCE(zl.beg_balance) + COALESCE(zl.debit,0) - COALESCE(zl.credit,0) as end_balance """ + \
                sql_select_grand_total + """
            FROM z_kg_gl_grand_total zl
            ) order by company_id, acc_code, row_no
        """
        final_query = query.format(
            date_from=init_date,company_id=current_company.id, sql_sort=sql_sort)
        self._cr.execute(final_query)
        data = cr.dictfetchall()
        # get grand total (first line in data query, since data ordered by acc_code)
        grand_total_row = data.pop(0)
        company_currency = current_company.currency_id
        grand_total = {
            "beg_balance": company_currency.round(grand_total_row.get('beg_balance', 0)),
            "debit": company_currency.round(grand_total_row.get('debit', 0)),
            "credit": company_currency.round(grand_total_row.get('credit', 0)),
            "balance": company_currency.round(grand_total_row.get('balance', 0)),
            "end_balance": company_currency.round(grand_total_row.get('running_total_balance', 0)),
        }
        return data, grand_total

    def query_get_clause(self):

        # used on calculating running total and row number
        sql_sort = "acc.company_id, acc.code"
        if self.report_type == 'sum':
            if self.sortby == 'sort_journal_partner':
                sql_sort += ", j.code, l.date"
            else:
                sql_sort += ", l.date, j.code"
        else:
            if self.sortby == 'sort_journal_partner':
                sql_sort += ", j.code, p.name, l.date, l.move_id"
            else:
                sql_sort += ", l.date"

        where_date = ""
        init_balance = False  # self.initial_balance
        # if init_balance and not start_date:
        #     raise UserError(_("You must define a Start Date"))

        if self.date_from:
            where_date += " AND l.date >= '" + self.date_from + "' "
            init_date = self.date_from
        else:
            init_date = '1900-01-01'

        if self.date_to:
            where_date += " AND l.date <= '" + self.date_to + "' "

        where_state = " AND m.state = 'posted' "
        if self.target_move == 'all':
            where_state = ""

        # where_display = "AND l.account_id IS NOT NULL "
        where_display = " AND (COALESCE(zl.balance,0) != 0 OR COALESCE(z.beg_balance,0) != 0)"
        having_display = ""
        # if self.display_account == 'not_zero':
        #     # having_display = "HAVING SUM(COALESCE(l.debit,0)) > 0 or SUM(COALESCE(l.credit, 0)) > 0 "
        #     having_display = ""
        # elif self.display_account == 'all':
        #     where_display = ""
        #     having_display = ""

        where_journal_id = ""

        if self.journal_ids:
            # ids = [journal.id for journal in
            #        self.env['account.journal'].search([('id', 'in', list(journal_ids._ids))])]
            ids = list(map(str, list(self.journal_ids._ids)))

            where_journal_id = " AND l.journal_id IN ( " + ', '.join(ids) + " ) "

        return sql_sort, where_journal_id, where_date, where_state, \
            where_display, having_display, init_date, init_balance

    def get_param(self):

        if self.journal_ids:
            codes = [journal.code for journal in
                     self.env['account.journal'].search([('id', 'in', self.journal_ids._ids)])]
        else:
            codes = None

        current_user = self.env['res.users'].browse(self.env.context.get('uid', False))
        current_company = current_user.company_id

        return codes, current_company

    def _define_report_name(self):
        """ path to report file)
        /app_name/path_to_file/report_name.mrt
        example: "/kg_report_base/static/rpt/RegistrationCard.mrt"
          kg_report_base is app name (module name)

        :return: str
        """
        if self.report_type == "det":
            rpt = "/kg_account/static/rpt/GeneralLedger.mrt"
        else:
            rpt = "/kg_account/static/rpt/GeneralLedgerSum.mrt"

        return rpt

        # return "/kg_report_base/static/rpt/sample1.mrt"

    def _define_report_variables(self):
        """ define report variables

        key : report variable name
        value : variable value to be send to report
        is_image: if value is an image or not

        :return: list of KgReportVariable
        """
        variables = list()

        # contoh menambahkan variable:
        # variables.append(KgReportVariable(
        #     key="Address1",  # variable name in report
        #     value="ini alamat jl bla bla",
        # ).to_dict())

        codes, current_company = self.get_param()

        variables.append(KgReportVariable(
            key="StartDate",  # variable name in report
            value=self.date_from if self.date_from else '',
        ).to_dict())

        variables.append(KgReportVariable(
            key="EndDate",  # variable name in report
            value=self.date_to if self.date_to else '',
        ).to_dict())

        variables.append(KgReportVariable(
            key="Display",  # variable name in report
            value=dict(self._fields['display_account'].selection).get(self.display_account),
        ).to_dict())

        if codes:
            journals = ', '.join(codes)
        else:
            journals = 'All'

        variables.append(KgReportVariable(
            key="Journal",  # variable name in report
            value=journals,
        ).to_dict())

        variables.append(KgReportVariable(
            key="Sort",  # variable name in report
            value=dict(self._fields['sortby'].selection).get(self.sortby),
        ).to_dict())

        variables.append(KgReportVariable(
            key="Target",  # variable name in report
            value=dict(self._fields['target_move'].selection).get(self.target_move),
        ).to_dict())

        variables.append(KgReportVariable(
            key="UserPrint",  # variable name in report
            value=self.env.user.name,
        ).to_dict())

        variables.append(KgReportVariable(
            key="Company",  # variable name in report
            value=current_company.name,
        ).to_dict())

        return variables


class KgReportVariable(object):

    def __init__(self, key, value, is_image=False, format_value="url"):
        self.key = key
        self.value = value
        self.is_image = is_image
        self.format_value = format_value  # this is format value for image (str or url path)

    def to_dict(self):
        return {
            "key": self.key,
            "value": self.value,
            "is_image": self.is_image,
            "format_value": self.format_value
        }
