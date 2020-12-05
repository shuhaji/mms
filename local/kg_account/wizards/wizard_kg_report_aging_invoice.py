
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo import http
from odoo.http import request
from odoo.modules import get_module_path
from datetime import datetime, timedelta
import json


class WizardAgingInvoice(models.TransientModel):
    _inherit = 'wizard.kg.report.base'
    _name = 'wizard.kg.report.aging.invoice'
    _title = "KG Report - Aging Invoice Detail"

    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
    date_from = fields.Date(string='Start Date', required=True, default=fields.Date.today())
    period_length = fields.Integer(string='Period Length (days)', required=True, default=30)
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')
    result_selection = fields.Selection([('receivable', 'Receivable Accounts'),
                                        ('payable', 'Payable Accounts'),
                                         ], string="Partner's", required=True, default='receivable')

    @api.multi
    def _get_data(self):
        get_aging_invoice = self.get_aging_invoice_data()
        self.report_has_logo = False  # sample report has logo

        data = {
            'config': {
                'company_id': self.company_id.id,
                'date_from': self.date_from,
                'period_length': self.period_length,
                'target_move': self.target_move,
                'result_selection': self.result_selection,
                'user_name': self.env.user.name,
            },
            'data': get_aging_invoice
        }

        return data

    @api.multi
    def get_aging_invoice_data(self):
        result_selection_clause, target_move_clause = self.query_get_clause()

        query = """                   
                with z_kg_aging_invoice as 
                (                    
                    select i.partner_id, rp.display_name, i.id , aml.invoice_id, i."number" as invoice_no,
                        i.move_name, i.app_source,
                        i.account_id, i."date",
                        i.amount_total_signed as amount_invoice,
                        sum(coalesce(pr.amount, 0)) as amount_paid,
                        i.amount_total_signed - sum(coalesce(pr.amount, 0)) as net_amount
                    from account_invoice i
                        left join account_account acc ON i.account_id = acc.id                           
                        left join account_move_line aml on aml.invoice_id = i.id and i.account_id = aml.account_id
                        left join account_partial_reconcile pr on 
                            """ + result_selection_clause + """ 
                            and pr.max_date <= '{date_from}'                                                 
                        left join account_move m ON m.id = aml.move_id 
                        left join res_partner rp ON rp.id = i.partner_id
                    where
                        i.company_id = {company_id} 
                        and i.date <= '{date_from}'
                            """ + target_move_clause + """
                        and acc.internal_type = '{result_selection}'  
                        and i.amount_total_signed > 0
                    group by i.partner_id, rp.display_name, i.id , aml.invoice_id, i."number", i.move_name, i.app_source, 
                        i.account_id, i."date", i.amount_total_signed
                    --having sum(i.amount_total_signed - coalesce(pr.amount, 0)) != 0  
                )
                select *,
                    (case when ('{date_from}' - a.date) <= {period_length} then a.net_amount else 0 end) as amount1, 
                    (case when  ('{date_from}' - a.date) BETWEEN ({period_length}+1) AND ({period_length}*2) then a.net_amount else 0 end) as amount2,  
                    (case when  ('{date_from}' - a.date) BETWEEN ({period_length}*2)+1 AND ({period_length}*3) then a.net_amount else 0 end) as amount3,  
                    (case when ('{date_from}' - a.date) > ({period_length}*3) then a.net_amount else 0 end) as amount4	
                 from z_kg_aging_invoice as a
                 where a.net_amount != 0                    
                 order by a.display_name, a.date;
                """
        final_query = query.format(
            company_id=self.company_id.id, date_from=self.date_from, period_length=self.period_length,
            result_selection=self.result_selection)

        self.env.cr.execute(final_query)
        aging_invoice = self.env.cr.dictfetchall()

        return aging_invoice

    def query_get_clause(self):
        result_selection_clause = ""
        if self.result_selection == 'payable':
            result_selection_clause = "pr.credit_move_id = aml.id"
        elif self.result_selection == 'receivable':
            result_selection_clause = "pr.debit_move_id = aml.id"

        target_move_clause = ""
        if self.target_move == 'posted':
            target_move_clause = "and m.state = 'posted'"
        elif self.target_move == 'all':
            target_move_clause = ""

        return result_selection_clause, target_move_clause

    @staticmethod
    def _define_report_name():
        return "/kg_account/static/rpt/AgingInvoice.mrt"
