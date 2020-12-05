from odoo import models, fields, api
from odoo.exceptions import except_orm, Warning, RedirectWarning
from datetime import date, datetime, timedelta


class ReportAPMutation(models.AbstractModel):
    _name = 'report.kg_account.report_ap_mutation'

    @api.model
    def get_report_values(self, docids, data=None):

        start_date = data['start_date']
        end_date = data['end_date']
        partner_list = []
        company_id = self.env['res.company'].browse(int(data['company_id']))
        # partner_id = self.env['res.partner'].browse(data['partner_id'])
        # account_id = self.env['account.account'].browse(int(data['account_id']))

        bg_inv_filter = [('type', '=', 'in_invoice'),
                         ('state', 'in', ['open', 'paid']),
                         ('date_invoice', '<', start_date),
                         ('company_id.id', '=', int(data['company_id']))]
        bg_credit_inv_filter = [('type', '=', 'in_refund'),
                                ('state', 'in', ['open', 'paid']),
                                ('date_invoice', '<', start_date),
                                ('company_id.id', '=', int(data['company_id']))]
        bg_payment_filter = [('partner_type', '=', 'supplier'),
                             ('state', 'in', ['posted', 'sent', 'reconciled']),
                             ('payment_date', '<', start_date),
                             ('company_id.id', '=', int(data['company_id']))]
        bg_adjustment_filter = [('partner_type', '=', 'supplier'),
                                ('writeoff_account_id', '<>', False),
                                ('state', 'in', ['posted', 'sent', 'reconciled']),
                                ('payment_date', '<', start_date),
                                ('company_id.id', '=', int(data['company_id']))]
        bg_wh_filter = [('state', 'in', ['due', 'paid']),
                        ('date', '<', start_date),
                        ('withholding_tax_id.company_id.id', '=', int(data['company_id']))]
        inv_filter = [('type', '=', 'in_invoice'),
                      ('state', 'in', ['open', 'paid']),
                      ('date_invoice', '>=', start_date),
                      ('date_invoice', '<=', end_date),
                      ('company_id.id', '=', int(data['company_id']))]
        credit_inv_filter = [('type', '=', 'in_refund'),
                             ('state', 'in', ['open', 'paid']),
                             ('date_invoice', '>=', start_date),
                             ('date_invoice', '<=', end_date),
                             ('company_id.id', '=', int(data['company_id']))]
        adjustment_filter = [('partner_type', '=', 'supplier'),
                              ('writeoff_account_id', '<>', False),
                              ('state', 'in', ['posted', 'sent', 'reconciled']),
                              ('payment_date', '>=', start_date),
                              ('payment_date', '<=', end_date),
                              ('company_id.id', '=', int(data['company_id']))]
        payment_filter = [('partner_type', '=', 'supplier'),
                          ('state', 'in', ['posted', 'sent', 'reconciled']),
                          ('payment_date', '>=', start_date),
                          ('payment_date', '<=', end_date),
                          ('company_id.id', '=', int(data['company_id']))]
        wh_filter = [('state', 'in', ['due', 'paid']),
                     ('date', '>=', start_date),
                     ('date', '<=', end_date),
                     ('withholding_tax_id.company_id.id', '=', int(data['company_id']))]

        if data['account_id']:
            bg_inv_filter.append(('account_id.id', '=', int(data['account_id'])))
            inv_filter.append(('account_id.id', '=', int(data['account_id'])))
            if not data['partner_id']:
                partners = self.env['res.partner'].search([('supplier', '=', True),
                                                           ('property_account_payable_id', '=', data['account_id'])])
                for p in partners.ids:
                    if p not in partner_list:
                        partner_list.append(p)
            else:
                for p in data['partner_id']:
                    if p not in partner_list:
                        partner_list.append(p)

        # search beginning inv
        bg_inv_ids = self.env['account.invoice'].search(bg_inv_filter)
        if not data['account_id']:
            for inv in bg_inv_ids:
                if inv.partner_id.id not in partner_list:
                    partner_list.append(inv.partner_id.id)
#
        # search beginning credit inv
        bg_credit_inv_ids = self.env['account.invoice'].search(bg_credit_inv_filter)
        if not data['account_id']:
            for ci in bg_credit_inv_ids:
                if ci.partner_id.id not in partner_list:
                    partner_list.append(ci.partner_id.id)

        # search begining payment
        bg_payment_ids = self.env['account.payment'].search(bg_payment_filter)
        bg_payment_ids = bg_payment_ids.filtered(lambda payment: ('POS' or 'pos') not in payment.name)
        if not data['account_id']:
            for inv in bg_payment_ids:
                if inv.partner_id.id not in partner_list:
                    partner_list.append(inv.partner_id.id)

        # search begining adjustment/write off
        bg_adjustment_ids = self.env['account.payment'].search(bg_adjustment_filter)
        bg_adjustment_ids = bg_adjustment_ids.filtered(lambda payment: ('POS' or 'pos') not in payment.name)
        if not data['account_id']:
            for adj in bg_adjustment_ids:
                if adj.partner_id.id not in partner_list:
                    partner_list.append(adj.partner_id.id)

        # search beginning withholding tax
        bg_wh_ids = self.env['withholding.tax.move'].search(bg_wh_filter)
        if not data['account_id']:
            for wh in bg_wh_ids:
                if wh.partner_id.id not in partner_list:
                    partner_list.append(wh.partner_id.id)

        # search new invoice (current period)
        inv_ids = self.env['account.invoice'].search(inv_filter)
        if not data['account_id']:
            for inv in inv_ids:
                if inv.partner_id.id not in partner_list:
                    partner_list.append(inv.partner_id.id)

        # search new credit invoice (current period)
        credit_inv_ids = self.env['account.invoice'].search(credit_inv_filter)
        if not data['account_id']:
            for ci in credit_inv_ids:
                if ci.partner_id.id not in partner_list:
                    partner_list.append(ci.partner_id.id)

        # search adjustment/write off (current period)
        adjustment_ids = self.env['account.payment'].search(adjustment_filter)
        adjustment_ids = adjustment_ids.filtered(lambda payment: ('POS' or 'pos') not in payment.name)
        if not data['account_id']:
            for adj in adjustment_ids:
                if adj.partner_id.id not in partner_list:
                    partner_list.append(adj.partner_id.id)

        # search payment (current period)
        payment_ids = self.env['account.payment'].search(payment_filter)
        payment_ids = payment_ids.filtered(lambda payment: ('POS' or 'pos') not in payment.name)
        if not data['account_id']:
            for p in payment_ids:
                if p.partner_id.id not in partner_list:
                    partner_list.append(p.partner_id.id)

        # search withholding tax (current period)
        wh_ids = self.env['withholding.tax.move'].search(wh_filter)
        if not data['account_id']:
            for wh in wh_ids:
                if wh.partner_id.id not in partner_list:
                    partner_list.append(wh.partner_id.id)

        # START LOOPING
        total_bg_balance = 0
        total_inv = 0
        total_credit_inv = 0
        total_payment = 0
        total_adjustment = 0
        total_withholding_tax = 0
        total_all = 0

        data_report = []

        for p in partner_list:
            partner_code = '-'
            partner_name = 'NO NAME'
            partner_account = 'NO NAME'
            partner_ids = self.env['res.partner'].browse(p)
            if partner_ids:
                partner_name = partner_ids.display_name
                partner_code = partner_ids.id
                partner_account = partner_ids.property_account_payable_id.name

            # BEGINNING BALANCE
            lines = bg_inv_ids.filtered(lambda r: r.partner_id.id == p)
            amount_bg_inv = sum(l.amount_total for l in lines)

            ci_lines = bg_credit_inv_ids.filtered(lambda r: r.partner_id.id == p)
            amount_bg_credit_inv = sum(l.amount_total for l in ci_lines)

            bg_adj_in = bg_adjustment_ids.filtered(lambda r: r.partner_id.id == p and r.payment_type == 'inbound')
            amount_bg_adjustment_in = sum(p.writeoff_amount for p in bg_adj_in)

            bg_adj_out = bg_adjustment_ids.filtered(lambda r: r.partner_id.id == p and r.payment_type == 'outbound')
            amount_bg_adjustment_out = sum(p.writeoff_amount for p in bg_adj_out)

            bg_payment_in = bg_payment_ids.filtered(lambda r: r.partner_id.id == p and r.payment_type == 'inbound')
            amount_bg_payment_in = sum(p.amount for p in bg_payment_in)

            bg_payment_out = bg_payment_ids.filtered(lambda r: r.partner_id.id == p and r.payment_type == 'outbound')
            amount_bg_payment_out = sum(p.amount for p in bg_payment_out)

            bg_whtax = bg_wh_ids.filtered(lambda r: r.partner_id.id == p)
            amount_bg_whtax = sum(wh.amount for wh in bg_whtax)

            amount_bg_balance = amount_bg_inv - amount_bg_credit_inv - amount_bg_payment_out + amount_bg_payment_in + amount_bg_adjustment_out - amount_bg_adjustment_in - amount_bg_whtax

            # AMOUNT BALANCE
            invoices = inv_ids.filtered(lambda r: r.partner_id.id == p)
            amount_inv = sum(l.amount_total for l in invoices)

            credit_invoices = credit_inv_ids.filtered(lambda r: r.partner_id.id == p)
            amount_credit_inv = sum(l.amount_total for l in credit_invoices)

            # Payment
            payments_in = payment_ids.filtered(lambda r: r.partner_id.id == p and r.payment_type == 'inbound')
            amount_payment_in = sum(payment.amount for payment in payments_in) or 0.0

            payments_out = payment_ids.filtered(lambda r: r.partner_id.id == p and r.payment_type == 'outbound')
            amount_payment_out = sum(payment.amount for payment in payments_out) or 0.0

            amount_payment = amount_payment_out - amount_payment_in

            # Adjustment
            adj_in = adjustment_ids.filtered(lambda r: r.partner_id.id == p and r.payment_type == 'inbound')
            amount_adjustment_in = sum(p.writeoff_amount for p in adj_in) or 0.0

            adj_out = adjustment_ids.filtered(lambda r: r.partner_id.id == p and r.payment_type == 'outbound')
            amount_adjustment_out = sum(p.writeoff_amount for p in adj_out) or 0.0

            amount_adjustment = amount_adjustment_out - amount_adjustment_in

            # Withholding Tax
            wh_tax = wh_ids.filtered(lambda r: r.partner_id.id == p)
            amount_whtax = sum(wh.amount for wh in wh_tax)

            if amount_bg_balance != 0 or amount_inv != 0 or amount_credit_inv != 0 or amount_payment != 0 or amount_adjustment != 0 or amount_whtax != 0:
                data_report.append({
                    'partner_code': partner_code,
                    'partner_name': partner_name,
                    'partner_account': partner_account,
                    'amount_bg_balance': amount_bg_balance,
                    'amount_inv': amount_inv,
                    'amount_credit_inv': amount_credit_inv,
                    'amount_payment': amount_payment,
                    'amount_adjustment': amount_adjustment,
                    'amount_whtax': amount_whtax,
                    'amount_total': amount_bg_balance + amount_inv - amount_credit_inv - amount_payment + amount_adjustment - amount_whtax,
                })

            total_bg_balance += amount_bg_balance
            total_inv += amount_inv
            total_credit_inv += amount_credit_inv
            total_payment += amount_payment
            total_adjustment += amount_adjustment
            total_withholding_tax += amount_whtax
            total_all = total_bg_balance + total_inv - total_credit_inv - total_payment + total_adjustment - total_withholding_tax

        data_total = []
        data_total.append(total_bg_balance)
        data_total.append(total_inv)
        data_total.append(total_credit_inv)
        data_total.append(total_payment)
        data_total.append(total_adjustment)
        data_total.append(total_withholding_tax)
        data_total.append(total_all)

        # sort data_report by its partner_name
        if data_report:
            sorted_data_report = sorted(data_report, key=lambda data: (data.get('partner_name') or ''))
            data_report = sorted_data_report

        return {
            'docs'      : data_report,
            'data_total': data_total,
            'start_date': start_date,
            'end_date'  : end_date,
            'company_id': company_id.name,
            # 'partner_id': partner_id.display_name,
            # 'account_id': account_id.name,
            'printed_by': self.env.user.name,
            'printed_on': (datetime.now() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S"),
        }

