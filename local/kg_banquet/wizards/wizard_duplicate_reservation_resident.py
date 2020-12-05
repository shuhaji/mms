from odoo import fields, models, api
from odoo.exceptions import except_orm, Warning, RedirectWarning, UserError


class DuplicateReservationResidentWizard(models.TransientModel):
    _name = 'duplicate.reservation.resident.wizard'

    def _get_active_resident(self):
        context = self.env.context
        if context.get('active_model') == 'banquet.reservation.resident':
            return context.get('active_id', False)
        return False

    # def _default_copies(self):
    #     order_obj = self.env['banquet.reservation.resident']
    #     reservation_res_id = self.env.context.get('active_id', False)
    #     if not reservation_res_id:
    #         return False
    #     else:
    #         return order_obj.browse(reservation_res_id).copies_value

    reservation_res_id = fields.Many2one(comodel_name="banquet.reservation.resident",
                           string="Reservation Resident Number", required=False, default=_get_active_resident, )
    copies_value = fields.Integer()

    @api.multi
    def copy_resident(self, default=None):
        self.ensure_one()
        for rec in self:
            if rec.copies_value == 0:
                raise UserError("Copy value must be more than 0 !!")
            for i in range(rec.copies_value):
                default = dict(default or {})
                default.update({
                    'name': self.env['ir.sequence'].next_by_code('banquet.reservation.residential.number'),
                    'state_reservation': 'draft'
                })
                rec.rescopy = self.reservation_res_id.copy(default)
        return rec.rescopy
