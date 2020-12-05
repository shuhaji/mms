from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ReservationFolioRevenue(models.Model):
    _name = 'banquet.reservation.folio.revenue'
    _description = "Banquet Folio Revenue"

    name = fields.Char(string='Name')
    account_id = fields.Many2one('account.account', 'Account')
    amount = fields.Monetary(string='Amount', required=True)
    base_amount = fields.Monetary(string='Base Amount', required=True)
    folio_id = fields.Many2one('banquet.reservation.folio', string='Reservation Folio')
    currency_id = fields.Many2one('res.currency')

    @api.one
    @api.constrains('amount')
    def _check_amount(self):
        if self.amount < 0:
            raise ValidationError(_('amount cannot be negative.'))

    # TODO define calculation base_amount and generate name based (F,B,O,RESdRoom)
