import os

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.modules import get_module_path
from datetime import datetime
import json


class WizardTrialBalance(models.TransientModel):
    _inherit = 'wizard.kg.report.general.ledger'
    _name = 'wizard.kg.report.trial.balance'
    _title = "KG Report - Trial Balance"

    # sortby = fields.Selection([('sort_date', 'Date'), ('sort_journal_partner', 'Journal & Partner')], string='Sort by',
    #                           required=True, default='sort_date')
    # journal_ids = fields.Many2many('account.journal', string='Journals', required=True,
    #                                # default=lambda self: self.env['account.journal'].search([])
    #                                )
    # display_account = fields.Selection([('all', 'All'), ('movement', 'With movements'),
    #                                     ('not_zero', 'With balance is not equal to 0'), ],
    #                                    string='Display Accounts', required=True, default='movement')
    # date_from = fields.Date(string='Start Date')
    # date_to = fields.Date(string='End Date')
    # target_move = fields.Selection([('posted', 'All Posted Entries'),
    #                                 ('all', 'All Entries'),
    #                                 ], string='Target Moves', required=True, default='posted')
    # report_type = fields.Selection([('sum', 'Summary'), ('det', 'Details'), ], 'Report Type',
    #                                required=True, default='det')

    @api.multi
    def _get_data(self):

        self.report_has_logo = True  # sample report has logo
        current_company = self.get_param()

        res = self.get_report_values(current_company)

        return {
            "data1": res
        }

    def get_report_values(self, current_company=None):

        cr = self.env.cr

        sql_sort, where_date, where_state, where_display, \
            init_date, init_balance = self.query_get_clause()

        query = """
                WITH z_kg_trial_balance_beg_balance AS (
                    SELECT l.account_id AS account_id, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS beg_balance
                    FROM account_move_line l
                        LEFT JOIN account_move m ON (l.move_id=m.id)                         
                    WHERE l.date < %s 
                        and l.company_id = %s                         
                        """ + where_state + """                                          
                    GROUP BY l.account_id
                ),
                z_kg_move_line as (
                    SELECT l.account_id ,                        
                    COALESCE(SUM(l.debit),0) AS debit, 
                    COALESCE(SUM(l.credit),0) AS credit, 
                    COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance
                    FROM account_move_line l                  
                    LEFT JOIN account_move m ON (l.move_id=m.id) 
                    LEFT JOIN account_journal j ON (l.journal_id=j.id)  
                    where l.company_id = %s  
                        """ + where_date + """
                        """ + where_state + """ 
                    GROUP by l.account_id
                    )
                SELECT acc."name" as acc_name, 
                    acc.code as acc_code,                     
                    COALESCE(z.beg_balance,0) AS beg_balance,                     
                    COALESCE(l.debit,0) AS debit, 
                    COALESCE(l.credit,0) AS credit, 
                    COALESCE(l.debit,0) - COALESCE((l.credit), 0) AS balance
                FROM account_account acc
                    LEFT JOIN z_kg_trial_balance_beg_balance z on (acc.id = z.account_id)
                    LEFT JOIN z_kg_move_line l ON (l.account_id = acc.id)                           
                WHERE acc.company_id = %s  
                    """ + where_display + """                  
                ORDER BY acc.code     

                """
        params = (init_date, current_company.id, current_company.id, current_company.id)
        self._cr.execute(query, params)
        data = cr.dictfetchall()

        return data

    def query_get_clause(self):

        sql_sort = "acc.code"
        # if self.sortby == 'sort_date' and self.report_type == 'det':
        #     sql_sort = "acc.code"
        # elif self.sortby == 'sort_journal_partner' and self.report_type == 'sum':
        #     sql_sort = "acc.code"
        # elif self.sortby == 'sort_journal_partner':
        #     sql_sort = "acc.code"

        where_date = ""
        init_balance = False  # self.initial_balance
        # if init_balance and not start_date:
        #     raise UserError(_("You must define a Start Date"))

        if self.date_from:
            where_date += "AND l.date >= '" + self.date_from + "' "
            init_date = self.date_from
        else:
            init_date = '1900-01-01'

        if self.date_to:
            where_date += "AND l.date <= '" + self.date_to + "' "

        where_state = "AND m.state = 'posted' "
        if self.target_move == 'all':
            where_state = ""

        where_display = "and (COALESCE(l.debit,0) > 0 or COALESCE(l.credit, 0) > 0 or COALESCE(z.beg_balance,0) != 0)"
        # having_display = ""
        # if self.display_account == 'not_zero':
        #     having_display = ""
        # elif self.display_account == 'all':
        #     where_display = ""
        #     having_display = ""

        return sql_sort, where_date, where_state, \
            where_display, init_date, init_balance

    def get_param(self):
        current_user = self.env['res.users'].browse(self.env.context.get('uid', False))
        current_company = current_user.company_id

        return current_company

    def _define_report_name(self):
        # if self.report_type == "det":
        #     rpt = "/kg_account/static/rpt/TrialBalanceSummary.mrt"
        # else:
        rpt = "/kg_account/static/rpt/TrialBalanceSummary.mrt"

        return rpt

    def _define_report_variables(self):
        variables = list()

        current_company = self.get_param()

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
