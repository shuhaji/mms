from odoo import models, fields, api
from odoo.exceptions import except_orm, Warning, RedirectWarning
from datetime import date, datetime, timedelta
import calendar
import time

class report_ar_mutation_pdf(models.AbstractModel):

    _name = 'report.kg_account.report_ar_mutation_pdf'

    @api.model
    def get_report_values(self, docids, data=None):    
        # month_range = calendar.monthrange(int(data['year']),data['period'])
        # start_date = str(data['year']) + '-' + str(data['period']).rjust(2,'0') + '-' + str(month_range[0]).rjust(2,'0')
        # end_date = str(data['year']) + '-' + str(data['period']).rjust(2,'0') + '-' + str(month_range[1]).rjust(2,'0')
        
        start_date = data['start_date']
        end_date = data['end_date']
        company_id = data['company_id']
        partner_list = []

        company_ids = self.env['res.company'].browse(int(data['company_id']))

        # search begining folio
        bg_folio_ids = self.env['account.invoice'].search([
            ('type', '=', 'out_invoice'),
            ('state', 'in', ['open', 'paid']),
            ('date_invoice', '<', start_date),
            ('company_id', '=', company_id),
            ])

        for inv in bg_folio_ids:
            if inv.partner_id.id not in partner_list:
                partner_list.append(inv.partner_id.id)

        # search beginning credit note
        bg_creditnote_ids = self.env['account.invoice'].search([
            ('type', '=', 'out_refund'),
            ('state', 'in', ['open', 'paid']),
            ('date_invoice', '<', start_date),
            ('company_id', '=', company_id),
            ])

        for cn in bg_creditnote_ids:
            if cn.partner_id.id not in partner_list:
                partner_list.append(cn.partner_id.id)

        # search begining adjustment/write off
        bg_adjustment_ids = self.env['account.payment'].search([
            # ('payment_type', '=', 'inbound'),
            ('partner_type', '=', 'customer'),
            ('writeoff_account_id', '<>', False),
            ('state', 'in', ['posted', 'sent', 'reconciled']),
            ('payment_date', '<', start_date),
            ('company_id', '=', company_id),
            ])

        bg_adjustment_ids = bg_adjustment_ids.filtered(lambda payment: ('POS' or 'pos') not in payment.name)

        for adj in bg_adjustment_ids:
            if adj.partner_id.id not in partner_list:
                partner_list.append(adj.partner_id.id)

        # search begining payment
        bg_payment_ids = self.env['account.payment'].search([
            # ('payment_type', '=', 'inbound'),
            ('partner_type', '=', 'customer'),
            ('state', 'in', ['posted', 'sent', 'reconciled']),
            ('payment_date', '<', start_date),
            ('company_id', '=', company_id),
            ('is_advance_payment', '=', False),
            ])

        bg_payment_ids = bg_payment_ids.filtered(lambda payment: ('POS' or 'pos') not in payment.name)

        for inv in bg_payment_ids:
            if inv.partner_id.id not in partner_list:
                partner_list.append(inv.partner_id.id)

        # search new invoice (current period)
        folio_ids = self.env['account.invoice'].search([
            ('type', '=', 'out_invoice'),
            ('state', 'in', ['open', 'paid']),
            ('date_invoice', '>=', start_date),
            ('date_invoice', '<=', end_date),
            ('company_id', '=', company_id),
            ])

        for inv in folio_ids:
            if inv.partner_id.id not in partner_list:
                partner_list.append(inv.partner_id.id)

        # search adjustment/write off (current period)
        adjustment_ids = self.env['account.payment'].search([
            # ('payment_type', '=', 'inbound'),
            ('partner_type', '=', 'customer'),
            ('writeoff_account_id', '<>', False),
            ('state', 'in', ['posted', 'sent', 'reconciled']),
            ('payment_date', '>=', start_date),
            ('payment_date', '<=', end_date),
            ('company_id', '=', company_id),
            ])

        adjustment_ids = adjustment_ids.filtered(lambda payment: ('POS' or 'pos') not in payment.name)

        for adj in adjustment_ids:
            if adj.partner_id.id not in partner_list:
                partner_list.append(adj.partner_id.id)

        # search payment (current period)
        payment_ids = self.env['account.payment'].search([
            # ('payment_type', '=', 'inbound'),
            ('partner_type', '=', 'customer'),
            ('state', 'in', ['posted', 'sent', 'reconciled']),
            ('payment_date', '>=', start_date),
            ('payment_date', '<=', end_date),
            ('company_id', '=', company_id),
            ('is_advance_payment', '=', False),
            ])

        payment_ids = payment_ids.filtered(lambda payment: ('POS' or 'pos') not in payment.name)

        for p in payment_ids:
            if p.partner_id.id not in partner_list:
                partner_list.append(p.partner_id.id)

        # search for credit note
        creditnote_ids = self.env['account.invoice'].search([
            ('type', '=', 'out_refund'),
            ('state', 'in', ['open', 'paid']),
            ('date_invoice', '>=', start_date),
            ('date_invoice', '<=', end_date),
            ('company_id', '=', company_id),
            ])

        for cn in creditnote_ids:
            if cn.partner_id.id not in partner_list:
                partner_list.append(cn.partner_id.id)


        #START LOOPING
        total_bg_folio = 0
        total_bg_payment = 0
        total_bg_creditnote = 0
        total_bg_adjustment = 0
        total_bg_balance = 0
        total_folio = 0
        total_payment = 0
        total_creditnote = 0
        total_adjustment = 0
        total_all = 0


        data_report = []

        for p in partner_list:
            partner_code = '-'
            partner_name = 'NO NAME'
            partner_ids = self.env['res.partner'].browse(p)
            if partner_ids:
                partner_name = partner_ids.name
                partner_code = partner_ids.id

            #BEGINNING BALANCE
            lines = bg_folio_ids.filtered(lambda r: r.partner_id.id == p)
            amount_bg_folio = sum(l.amount_total for l in lines)

            bg_cn = bg_creditnote_ids.filtered(lambda r: r.partner_id.id == p)
            amount_bg_creditnote = sum(l.amount_total for l in bg_cn)

            bg_adj_in = bg_adjustment_ids.filtered(lambda r: r.partner_id.id == p and r.payment_type == 'inbound')
            amount_bg_adjustment_in = sum(p.writeoff_amount for p in bg_adj_in)

            bg_adj_out = bg_adjustment_ids.filtered(lambda r: r.partner_id.id == p and r.payment_type == 'outbound')
            amount_bg_adjustment_out = sum(p.writeoff_amount for p in bg_adj_out)

            bg_payment_in = bg_payment_ids.filtered(lambda r: r.partner_id.id == p and r.payment_type == 'inbound')
            amount_bg_payment_in = sum(p.amount for p in bg_payment_in)

            bg_payment_out = bg_payment_ids.filtered(lambda r: r.partner_id.id == p and r.payment_type == 'outbound')
            amount_bg_payment_out = sum(p.amount for p in bg_payment_out)

            amount_bg_balance = amount_bg_folio - amount_bg_creditnote - amount_bg_payment_in + amount_bg_payment_out - amount_bg_adjustment_in + amount_bg_adjustment_out

            #AMOUNT BALANCE
            # custom code by andi
            invoices = folio_ids.filtered(lambda r: r.partner_id.id == p)
            amount_folio = sum(l.amount_total for l in invoices)
            # end of custom code

            #PAYMENT BALANCE
            # custom code by andi
            # amount_adv_payments = 0.0
            # amount_total_invoices = sum(invoice.amount_total for invoice in invoices) or 0.0
            # amount_residual_invoices = sum(invoice.residual for invoice in invoices) or 0.0

            # code for compute the amount of adv payment used for the invoice if someday needed
            # for invoice in invoices:
            #     adv_payment_amount_used = 0.0
            #     for adv_payment in invoice.advance_payment_ids:
            #         adv_payment_amount_used = adv_payment.amount - adv_payment.residual_temp
            #         amount_adv_payments +=  adv_payment_amount_used
            # end of code

            # amount_payment = amount_total_invoices - amount_residual_invoices
            payments_in = payment_ids.filtered(lambda r: r.partner_id.id == p and r.payment_type == 'inbound')
            amount_payment_in = sum(payment.amount for payment in payments_in) or 0.0

            payments_out = payment_ids.filtered(lambda r: r.partner_id.id == p and r.payment_type == 'outbound')
            amount_payment_out = sum(payment.amount for payment in payments_out) or 0.0

            amount_payment = amount_payment_in - amount_payment_out

            # end of custom code

            # origin code by mas mario
            # lines = payment_ids.filtered(lambda r: r.partner_id.id == p)
            # amount_payment = sum(l.amount for l in lines)
            # end of origin code
            
            # CreditNote
            lines = creditnote_ids.filtered(lambda r: r.partner_id.id == p)
            amount_creditnote = sum(l.amount_total for l in lines)

            # Adjustment
            adj_in = adjustment_ids.filtered(lambda r: r.partner_id.id == p and r.payment_type == 'inbound')
            amount_adjustment_in = sum(p.writeoff_amount for p in adj_in) or 0.0

            adj_out = adjustment_ids.filtered(lambda r: r.partner_id.id == p and r.payment_type == 'outbound')
            amount_adjustment_out = sum(p.writeoff_amount for p in adj_out) or 0.0

            amount_adjustment = amount_adjustment_in - amount_adjustment_out
            
            data_report.append({
                'partner_code'          : partner_code,
                'partner_name'          : partner_name,
                'amount_bg_balance'     : amount_bg_balance,
                'amount_folio'          : amount_folio,
                'amount_payment'        : amount_payment,
                'amount_creditnote'     : amount_creditnote,
                'amount_adjustment'     : amount_adjustment,
                'amount_total'          : amount_bg_balance + amount_folio - amount_creditnote - amount_adjustment - amount_payment,
                })

            total_bg_balance    += amount_bg_balance
            total_folio         += amount_folio
            total_payment       += amount_payment
            total_creditnote    += amount_creditnote
            total_adjustment    += amount_adjustment
            total_all = total_bg_balance + total_folio - total_creditnote - total_payment - total_adjustment

        data_total = []
        data_total.append(total_bg_balance)
        data_total.append(total_folio)
        data_total.append(total_creditnote)
        data_total.append(total_payment)
        data_total.append(total_adjustment)
        data_total.append(total_all)

        # custom code by andi to sort data_report by its partner_name
        if data_report:
            sorted_data_report = sorted(data_report, key=lambda data: (data.get('partner_name') or ''))
            data_report = sorted_data_report
        # end of custom code

        return {
            'docs'      : data_report,
            'data_total': data_total,
            'start_date': start_date,
            'end_date'  : end_date,
            'company_id': company_ids.name,
            'printed_by': self.env.user.name,
            'printed_on': (datetime.now() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S"),
        }

