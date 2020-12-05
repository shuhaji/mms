from odoo import api,fields,models,_ 
from odoo.exceptions import UserError
from datetime import datetime
import time

class KGVoucherPayable(models.TransientModel):
    _name = 'voucher.payable.wizard'

    name = fields.Char(
        'Name',
    )

    partner_id = fields.Many2one(
        'res.partner', 
        'Partner', 
    )

    start_date = fields.Date(
        'Start Date',
    )

    end_date = fields.Date(
        'End Date',
    )

    current_date = fields.Date(
        'Current Date',
        default=fields.Date.today()
    )

    @api.multi
    def print_report(self):
        for voucher in self:
            data = {
                'ids': voucher.ids,
                'model': voucher,
                'model_name': voucher._name,
            }
            return self.env.ref('kg_account.voucher_payable_report_action').report_action(self, data=data)
    
    # @api.multi
    # def get_vendor_bills(self):
    #     for voucher in self:
    #         valid_vendor_bill = valid_vendor_bill = self.env['account.invoice'].search([('type', '=', 'in_invoice'), ('date_due', '<=', report_model.start_date), ('partner_id', '=', report_model.partner_id.id)])
    #         import pdb; pdb.set_trace()
    #         return valid_vendor_bill

class KGVoucherPayableReport(models.AbstractModel):
    _name = 'report.kg_account.voucher_payable_report'

    @api.multi
    def get_report_values(self, docids, data=None):
        if data:
            ids = data['ids']
            report_model = self.env[data['model_name']].browse(ids)
            valid_vendor_bill = self.env['account.invoice'].search(
                [('type', '=', 'in_invoice'),
                ('state', '=', 'open'),
                ('date_due', '>=', report_model.start_date), 
                ('date_due', '<=', report_model.end_date), 
                ('partner_id', '=', report_model.partner_id.id)]
            )
            
            docargs = {
                'doc_ids': report_model.ids,
                'doc_model': data['context']['active_model'],
                'docs': report_model,
                'vendor': valid_vendor_bill,
            }
            
            data['vendor'] = valid_vendor_bill
            return docargs