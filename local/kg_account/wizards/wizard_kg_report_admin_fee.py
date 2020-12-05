
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo import http
from odoo.http import request
from odoo.modules import get_module_path
from datetime import datetime, timedelta
import json


class WizardAdminFee(models.TransientModel):
    _inherit = 'wizard.kg.report.base'
    _name = 'wizard.kg.report.admin.fee'
    _title = "KG Report - Administration Fee"

    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id.id)
    start_date = fields.Date(string='Start Date', required=True, default=fields.Date.today())
    end_date = fields.Date(string='End Date', required=True, default=fields.Date.today())
    # result_selection = fields.Selection([('receivable', 'Receivable Accounts'),
    #                                     ('payable', 'Payable Accounts'),
    #                                      ], string="Partner's", required=True, default='receivable')

    @api.multi
    def _get_data(self):
        get_admin_fee = self.get_admin_fee_data()
        self.report_has_logo = False  # sample report has logo

        data = {
            'config': {
                'company_id': self.company_id.id,
                'start_date': self.start_date,
                'end_date': self.end_date,
                # 'result_selection': self.result_selection,
                'user_name': self.env.user.name,
                'company_name': self.company_id.name,
            },
            'data': get_admin_fee
        }

        return data

    @api.multi
    def get_admin_fee_data(self):
        # result_selection_clause = self.query_get_clause()

        query = """                          
                select ap.company_id, ap.payment_type, aa.code as account_code, aa."name" as account_name, 
                    ap.payment_date as trxdate, coalesce(ap.move_name,'') as move_name, ap.writeoff_amount as amount, rp.display_name as login
                from account_payment ap 
                    left join account_account aa on ap.writeoff_account_id = aa.id
                    left join res_users ru on ap.write_uid = ru.id
                    left join res_partner rp on ru.partner_id = rp.id
                where ap.writeoff_amount!=0 
                    and ap.company_id = {company_id}
                    and ap.payment_date between '{start_date}' and '{end_date}'
                    and ap.state in ('posted', 'sent', 'reconciled')
                union 	
                select ap.company_id, ap.payment_type, aa.code as account_code, aa."name" as account_name, 
                    apl.admin_date as trxdate, coalesce(ap.move_name,'') as move_name, apl.amount as amount, rp.display_name as login 
                from account_payment_line apl 
                    left join account_payment ap on apl.payment_id = ap.id
                    left join account_account aa on apl.account_id = aa.id
                    left join res_users ru on apl.write_uid = ru.id
                    left join res_partner rp on ru.partner_id = rp.id
                where apl.amount != 0
                    and ap.company_id = {company_id}
                    and apl.admin_date between '{start_date}' and '{end_date}'
                    and ap.state in ('posted', 'sent', 'reconciled')
                order by account_name, trxdate, move_name
                """
        final_query = query.format(
            company_id=self.company_id.id, start_date=self.start_date, end_date=self.end_date)

        self.env.cr.execute(final_query)
        admin_fee = self.env.cr.dictfetchall()

        return admin_fee

    # def query_get_clause(self):
    #     result_selection_clause = ""
    #     if self.result_selection == 'payable':
    #         result_selection_clause = "pr.credit_move_id = aml.id"
    #     elif self.result_selection == 'receivable':
    #         result_selection_clause = "pr.debit_move_id = aml.id"
    #
    #     return result_selection_clause

    @staticmethod
    def _define_report_name():
        return "/kg_account/static/rpt/AdminFee.mrt"
