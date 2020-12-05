from odoo import api, fields, models


class KGPosOutlet(models.TransientModel):
    _name = 'pos.outlet'

    working_date = fields.Date('Working Date', default=fields.Date.context_today)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id.id)
    shift_id = fields.Many2one(comodel_name='hr.shift', string='Shift')

    @api.multi
    def print_report(self):
        data = {
            'working_date': self.working_date,
            'company_id': self.company_id.id,
            'company_name': self.company_id.name,
            'shift_id': self.shift_id.id,
            'shift_desc': self.shift_id.description,
        }
        return self.env.ref('kg_pos.menu_report_pos_outlet').report_action([], data=data)


