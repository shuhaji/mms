import time
from odoo import api, models, _
from odoo.exceptions import UserError

class KGReportGeneralLedger(models.AbstractModel):
    _inherit = 'report.account.report_generalledger'

    @api.model
    def get_report_values(self, docids, data=None):
        res = super(KGReportGeneralLedger, self).get_report_values(docids, data=data)
        beg_balance_amount = 0.0 
        current_user = self.env['res.users'].browse(self.env.context.get('uid', False))
        current_company = current_user.company_id
        date_from = False

        if data:     
            date_from = data['form']['used_context']['date_from']


        if res.get('Accounts', False):
            data_accounts = res['Accounts']
            for account in data_accounts:
                if account.get('move_lines', []):
                    # for line in account['move_lines']:
                        # if (line['debit'] or line['credit']) > 0:
                    if all((line['debit'] or line['credit']) > 0 for line in account['move_lines']):
                        move_line = self.env['account.move.line'].search(
                            [
                            ('account_id.name', '=', account['name']),
                            ('company_id', '=', current_company.id),
                            ('date', '<', date_from),
                            ]
                        )
                        total_debit = sum(l.debit for l in move_line) or 0.0
                        total_credit = sum(l.credit for l in move_line) or 0.0
                        account['beg_balance'] = total_debit - total_credit or 0.0
        
        return res
