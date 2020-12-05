from odoo import api,fields,models,_ 
from odoo.exceptions import UserError
from datetime import datetime
import time

class KGInvoiceVerificationRegister(models.TransientModel):
    _name = 'invoice.verification.register'

    name = fields.Char(
        'name'
    )

    partner_id = fields.Many2one(
        'res.partner', 
        'Partner',
    )

    start_date = fields.Date(
        'Start Date',
        default=fields.Date.today()
    )

    end_date = fields.Date(
        'End Date',
        default=fields.Date.today()
    )

    current_date = fields.Date(
        'Current Date',
        default=fields.Date.today(),
    )

    user_id = fields.Many2one(
        'res.users',
        'User ID',
    )
    
    @api.model
    def default_get(self, fields):
        res = super(KGInvoiceVerificationRegister, self).default_get(fields)
        current_user = self.env['res.users'].browse(self.env.context.get('uid', False))
        res['user_id'] = current_user.id
        return res

    @api.multi
    def print_report(self):
        for invoice_register in self:
            data = {
                'ids': invoice_register.ids,
                'model': invoice_register,
                'model_name': invoice_register._name,
            }

            return self.env.ref('kg_account.invoice_verification_register_report_action').report_action(self, data=data)


class KGInvoiceVerificationRegisterReport(models.AbstractModel):
    _name = 'report.kg_account.invoice_verification_register_report'

    @api.multi
    def get_report_values(self, docids, data=None):
        if data:
            ids = data['ids']
            report_model = self.env[data['model_name']].browse(ids)
            if report_model.partner_id:
                valid_vendor_bill = self.env['account.invoice'].search(
                    [('type', '=', 'in_invoice'), 
                    ('partner_id', '=', report_model.partner_id.id),
                    ('date_invoice', '>=', report_model.start_date), 
                    ('date_invoice', '<=', report_model.end_date),
                    ('state', 'not in', ['draft', 'cancel'])], order='number'
                )

            if not report_model.partner_id:
                valid_vendor_bill = self.env['account.invoice'].search(
                    [('type', '=', 'in_invoice'), 
                    ('date_invoice', '>=', report_model.start_date), 
                    ('date_invoice', '<=', report_model.end_date),
                    ('state', 'not in', ['draft', 'cancel'])], order='number'
                )
            
            if not valid_vendor_bill:
                raise UserError(_('There is no invoice within the range of start and end date'))

            docargs = {
                'doc_ids': report_model.ids,
                'doc_model': data['context']['active_model'],
                'docs': report_model,
                'vendor': valid_vendor_bill,
            }

            return docargs
