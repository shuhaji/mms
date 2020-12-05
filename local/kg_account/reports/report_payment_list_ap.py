from odoo import models, fields, api
from odoo.exceptions import except_orm, Warning, RedirectWarning
from datetime import date, datetime, timedelta
import calendar
import time


class report_payment_list_ap(models.AbstractModel):

    _name = 'report.kg_account.report_payment_list_ap'

    @api.model
    def get_report_values(self, docids, data=None):
        # search payment
        payment_ids = self.env['account.payment'].search([
            ('payment_type', '=', 'outbound'),
            ('state', 'in', ['sent', 'posted', 'reconciled']),
            ('payment_date', '>=', data['date']),
            ('payment_date', '<=', data['date']),
            ('company_id.id', '=', int(data['company_id'])),
            ('journal_id', '=', data['journal_id'])
            ])

        payment_ids = payment_ids.filtered(lambda payment: ('POS' or 'pos') not in payment.name)

        data_report = []
        total = 0

        model_name = self.env.context.get('active_model', False)
        model_ids = self.env.context.get('active_ids', [])
        report_model = self.env[model_name].browse(model_ids)

        for p in payment_ids:
            move_ids = self.env['account.move.line'].search([
                ('payment_id', '=', p.id),
                ('credit', '>', 0),
                ('company_id', '=', int(data['company_id']))
            ])

            if len(p.invoice_ids) == 1:
                partner_name = p.partner_id.name

                # custom code by andi
                if p.partner_id.parent_id:
                    partner_name = p.partner_id.parent_id.name
                # end of code

                # invoice_number = m.ref
                invoice_number = p.communication

                if not partner_name:
                    partner_name = move_ids[0].partner_id.name

                if not invoice_number:
                    invoice_number = move_ids[0].ref

                data_report.append({
                    'payment_date': p.payment_date,
                    'payment_reference': p.name,
                    'partner_name': partner_name,
                    'invoice_number': invoice_number,
                    'amount_total': p.amount,
                    'user': p.write_uid.name,
                    })

                total += p.amount
                
            # search payment by journal
            else:
                for m in move_ids:
                    # custom code by andi
                    partner_name = m.partner_id.name or ''
                    if m.partner_id.parent_id:
                        partner_name = m.partner_id.parent_id.name or ''
                    # end of code

                    data_report.append({
                        'payment_date': p.payment_date,
                        'payment_reference': p.name,

                        # original code
                        # 'partner_name': m.partner_id.name,
                        # end of original code

                        # custom code by andi
                        'partner_name': partner_name,
                        # end of code

                        'invoice_number': m.ref,
                        'amount_total': m.credit,
                        'user': p.create_uid.name,
                        })
                    total += m.credit

        if data_report:
            sorted_data_report = sorted(data_report, key=lambda data: (data.get('partner_name') or ''))
            data_report = sorted_data_report

        return {
            'docs': data_report,
            'grand_total': total,
            'date': data['date'],
            'company_id': self.env['res.company'].browse(int(data['company_id'])).name,
            'printed_by': self.env.user.name,
            'printed_on': (datetime.now() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S"),
            'payment_journal': report_model.journal_id,
        }

