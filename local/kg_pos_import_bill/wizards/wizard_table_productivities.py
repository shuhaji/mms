from odoo import api,fields,models
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


def get_years():
    year_list = []
    for i in range(2010, 2050):
        year_list.append((i, str(i)))
    return year_list


class KGTableProductivities(models.TransientModel):
    _name = 'table.productivities'

    bulan = fields.Selection([(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
                              (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
                              (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December'), ],
                             string='Month',default=(datetime.now() + timedelta(hours=7)).month)
    tahun = fields.Selection(get_years(), string='Year', default=(datetime.now() + timedelta(hours=7)).year)

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

    @api.multi
    @api.onchange('bulan', 'tahun')
    def get_periode_to_date(self):
        for doc in self:
            doc.start_date = datetime.strptime(str(doc.tahun) + '-' + str(doc.bulan) + '-' + '1', '%Y-%m-%d')
            doc.end_date = datetime.strptime(str(doc.tahun) + '-' + str(doc.bulan) + '-' + '1', '%Y-%m-%d')+relativedelta(months=1)-timedelta(days=1)

    @api.multi
    def print_report(self):
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'bulan': dict(self._fields['bulan'].selection).get(self.bulan),
            'tahun': self.tahun,
        }
        return self.env.ref('kg_pos_import_bill.menu_report_table_productivities').report_action([], data=data)


