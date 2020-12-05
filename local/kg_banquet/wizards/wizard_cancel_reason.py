from odoo import fields, models, api


class CancelReasonWizard(models.TransientModel):
    _name = 'wizard.cancel.reason.banquet.reservation'

    cancel_reason = fields.Text(string='Cancel Reason', required=True)
    reservation_id = fields.Many2one('banquet.reservation', string='Banquet Reservation ID')

    @api.multi
    def button_confirm(self):
        self.reservation_id.write({
            'state': 'release',
            'cancel_reason': self.cancel_reason,
            'is_release': True,
        })
