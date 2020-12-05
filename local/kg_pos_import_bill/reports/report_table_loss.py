from odoo import models, api, fields
from datetime import datetime, timedelta


class ReportTableLoss(models.AbstractModel):
    _name = 'report.kg_pos_import_bill.report_table_loss'

    @api.model
    def get_report_values(self, docids,  data=None):
        start_date = data['start_date']
        end_date = data['end_date']
        bulan = data['bulan']
        tahun = data['tahun']

        # search table_loss (current period)
        table_loss_data = self.env['kg.pos.order.reservation'].search([
            ('is_reservation', '=', 'True'),
            ('state_reservation', '=', 'cancel'),
            ('date_order', '>=', start_date),
            ('date_order', '<=', end_date),
        ], order='reservation_time_start, company_name')

        return {
            'docs': table_loss_data,
            'start_date': start_date,
            'end_date': end_date,
            'bulan': bulan,
            'tahun': tahun,
            'printed_by': self.env.user.name,
            'printed_on': (datetime.now() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S"),
        }