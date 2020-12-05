from odoo import models, fields, api
from odoo.exceptions import except_orm, Warning, RedirectWarning
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools.safe_eval import safe_eval


class wizard_kg_pos_cancel_reservation(models.TransientModel):
    _name = 'wizard.kg.pos.cancel.reservation'

    reservation_id = fields.Many2one(comodel_name='kg.pos.order.reservation', string='Reservation Number', readonly=True)
    contact_person = fields.Many2one(comodel_name='res.partner', string="Contact Person", readonly=True)
    customer_count = fields.Integer('Guests', readonly=True)
    # table_id        = fields.Many2one(comodel_name='restaurant.table',string="Table No.", readonly=True)
    cancel_reason = fields.Text(string="Cancel Reason", required=True)
    
    @api.multi
    def button_confirm(self):
        for rec in self.reservation_id.table_list:
            if rec.is_waiting_list:
                rec.write({'is_waiting_list': False})

            rec.reservation_id.recheck_oldest_waiting_list_orders(
                rec.reservation_id.id, rec.table_id.id,
                rec.reservation_id.reservation_time_start, rec.reservation_id.reservation_time_end)

        self.reservation_id.write({
            'cancel_reason': self.cancel_reason,
            'state_reservation': 'cancel',
            'cancel_time': fields.datetime.now(),
            'cancel_by': self.env.user.id,
            })
