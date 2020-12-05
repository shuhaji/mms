from odoo import models, api
from datetime import datetime, timedelta


class ReportTableReservationList(models.AbstractModel):
    _name = 'report.kg_pos_import_bill.report_table_reservation_list'

    @api.model
    def get_report_values(self, docids,  data=None):
        start_date = data['start_date']
        end_date = data['end_date']

        # search table_reservation (current period)
        table_reservation_ids = self.env['kg.pos.order.reservation'].search([
            ('is_reservation', '=', 'True'),
            ('date_order', '>=', start_date),
            ('date_order', '<=', end_date),
        ])

        data_report = []

        for x in table_reservation_ids:
            data_report.append({
                'name': x.name,
                'reservation_time_start': x.reservation_time_start, #datetime.strptime(x.reservation_time_start, '%Y-%m-%d %H:%M:%S') + timedelta(hours=7),
                'reservation_time_end': x.reservation_time_start, #datetime.strptime(x.reservation_time_end, '%Y-%m-%d %H:%M:%S') + timedelta(hours=7),
                'event_name': x.event_name,
                'company_name': x.company_name.name,
                'table_label': x.table_label or ' ',
                'customer_count': x.customer_count,
                'state_reservation': x.state_reservation,
                'partner_id': x.partner_id.name,
                'salesperson_id': x.salesperson_id.name,
            })

        # custom code to sort data_report by its time start, company, table
        if data_report:
            sorted_data_report = sorted(data_report, key=lambda data: (data.get('reservation_time_start', ''),
                                                                       data.get('company_name', ''),
                                                                       data.get('table_label', '')
                                                                       )
                                        )
            data_report = sorted_data_report

        return {
            'docs': data_report,
            'start_date': start_date,
            'end_date': end_date,
            'printed_by': self.env.user.name,
            'printed_on': (datetime.now() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S"),
        }