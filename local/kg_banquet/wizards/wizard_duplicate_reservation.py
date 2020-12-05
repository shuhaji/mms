from odoo import fields, models, api
from odoo.exceptions import except_orm, Warning, RedirectWarning, UserError


class DuplicateReservationWizard(models.TransientModel):
    _name = 'duplicate.reservation.wizard'

    def _get_active_reservation(self):
        context = self.env.context
        if context.get('active_model') == 'banquet.reservation':
            return context.get('active_id', False)
        return False

    reservation_id = fields.Many2one(comodel_name="banquet.reservation", string="Reservation Number", required=False, default=_get_active_reservation, )
    copies_value = fields.Integer(default=1)

    @api.multi
    def copy_reservation(self, default=None):
        self.ensure_one()
        for rec in self:
            if rec.copies_value == 0:
                raise UserError("Copy value must be more than 0 !!")
            for i in range(rec.copies_value):
                default = dict(default or {})
                default.update({
                    # 'name': self.env['ir.sequence'].next_by_code('banquet.reservation.name'),
                    'state': 'draft',
                    'cancel_reason': ''
                })
                rec.rescopy = self.reservation_id.copy(default)
        return rec.rescopy
