from odoo import models, api
from datetime import datetime, timedelta


class ReportPayments(models.AbstractModel):
    _name = 'report.kg_account.report_payments'

    @api.model
    def get_report_values(self, docids,  data=None):
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        company_id = data['form']['company'][0]
        journal_id = data['form']['journal_id'][0]

        company_ids = self.env['res.company'].browse(company_id)
        journal_ids = self.env['account.journal'].browse(journal_id)

        # search payment (current period)
        payment_ids = self.env['account.payment'].search([
            # ('payment_type', '=', 'inbound'),
            ('partner_type', '=', 'customer'),
            ('state', 'in', ['posted', 'sent', 'reconciled']),
            ('payment_date', '>=', date_from),
            ('payment_date', '<=', date_to),
            ('company_id.id', '=', company_id),
            ('journal_id.id', '=', journal_id),
        ])

        payment_ids = payment_ids.filtered(lambda payment: ('POS' or 'pos') not in payment.name)

        # total_payment = 0
        data_report = []
        # data_total = []
        # inv_number = ''
        # amount_total_signed = 0

        for p in payment_ids:

            for inv in p.invoice_ids:
                inv_number = inv.number
                # amount_total_signed = inv.amount_total_signed
                if p.payment_type == 'outbound':
                    amount_total_signed = -1 * inv.amount_total_signed
                else:
                    amount_total_signed = inv.amount_total_signed

                for mv in p.move_line_ids:
                    if mv.credit > 0:
                        credit_account = mv.account_id

                        data_report.append({
                            'payment_date': p.payment_date,
                            'name': p.name,
                            'invoice_ids': inv_number,
                            'folio': '',
                            'company': p.partner_id.name,
                            'amount': amount_total_signed,
                            'user': p.create_uid.name,
                            'credit_account_code': credit_account.code,
                            'credit_account_name': credit_account.name,
                        })

                    # total_payment += amount_total_signed

        # data_total.append(total_payment)

        # sort data_report by its payment_date
        if data_report:
            sorted_data_report = sorted(data_report, key=lambda data: (data.get('payment_date') or ''))
            data_report = sorted_data_report

        return {
            'docs': data_report,
            # 'data_total': data_total,
            'start_date': date_from,
            'end_date': date_to,
            'company': company_ids.name,
            'journal': journal_ids.name,
            'debit_account_code': journal_ids.default_debit_account_id.code,
            'debit_account_name': journal_ids.default_debit_account_id.name,
            'printed_by': self.env.user.name,
            'printed_on': (datetime.now() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S"),
        }