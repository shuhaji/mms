import copy
import os

from dateutil import parser

from odoo import api,fields,models,http,_
from odoo.modules import get_module_path
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import json


class WizardKgReportAgingCreditAcquirer(models.TransientModel):
    _inherit = ['wizard.kg.report.base']
    _name = 'wizard.kg.report.aging_credit_acquirer'
    _title = "KG Report - Aging Acquirer"

    date_from = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    option_type = fields.Selection(
        [('Summary', 'Summary'),
         ('Detail', 'Detail'),
         ],
        string='Select Option',
        required=True,
        default='Summary')

    @api.multi
    def _get_data(self):
        """ get data from database or any other source

        :return: dict or list of dict
        """
        # extract financial report data
        now = datetime.utcnow()+timedelta(hours=7)
        get_aging_credit_acquirer = self.get_aging_credit_acquirer_data()
        blank_name = "..........................."
        self.report_has_logo = False  # sample report has logo
        data = {
            "config": {
                "date_from": self.date_from,
                "company_name": self.env.user.company_id.name,
                "prepared_by": self.env.user.name or blank_name,
                "print_date": now.strftime("%Y-%m-%d %H:%M"),
                "option_type": self.option_type,
            },
            "data": get_aging_credit_acquirer
        }

        # return self._sample_data_reg_card()
        return data

    @api.multi
    def get_aging_credit_acquirer_data(self):
        result_selection_clause = self.query_get_clause()
        date_from = self.date_from
        # get pos transaction data for Daily Card Report
        query = """select p.journal_id, """ + result_selection_clause + """ aj."name" as journal_name,
        coalesce(p.kg_issuer_type_id, 0) as kg_issuer_type_id,
        coalesce(it."name", 'Others') as kg_issuer_type_name,
        sum(case when ('""" + date_from + """' - coalesce(p.date, a.date)) < 31 then a.amount else 0 end) as amount1,
        sum(case when ('""" + date_from + """' - coalesce(p.date, a.date)) between 31 and 60 then a.amount else 0 end) as amount2,
        sum(case when ('""" + date_from + """' - coalesce(p.date, a.date)) between 61 and 90 then a.amount else 0 end) as amount3,
        sum(case when ('""" + date_from + """' - coalesce(p.date, a.date)) > 90 then a.amount else 0 end) as amount4
        from kg_acquirer_transaction a
        left join account_journal aj on aj.id = a.journal_id
        left join kg_issuer_type it on it.id = a.kg_issuer_type_id
        left join kg_acquirer_transaction p on p.id = coalesce(a.apply_id, a.id)
        left join account_payment ap on ap.id = a.payment_id
        where a.date <= '""" + date_from + """' and (a.type = 1 or ap.state in ('posted','sent','reconciled'))
        group by p.journal_id,""" + result_selection_clause + """ aj.name, p.kg_issuer_type_id, it.name
        having sum(a.amount) != 0 
        order by """ + result_selection_clause + """ aj.name, coalesce(it."name", 'Others')"""
        self.env.cr.execute(query)
        aging_credit_acquirer_summary = self.env.cr.dictfetchall()

        return aging_credit_acquirer_summary

    def query_get_clause(self):
        result_selection_clause = ""
        if self.option_type == 'Summary':
            result_selection_clause = ""
        elif self.option_type == 'Detail':
            result_selection_clause = " p.date, p.name,"

        return result_selection_clause

    def _define_report_name(self):
        if self.option_type == 'Summary':
            return_result = "/kg_account/static/rpt/AgingCreditAcquirerSummary.mrt"
        elif self.option_type == 'Detail':
            return_result = "/kg_account/static/rpt/AgingCreditAcquirerDetail.mrt"
        return return_result
