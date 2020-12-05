from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ReservationFolio(models.Model):
    _name = 'banquet.reservation.folio'
    _description = "Reservation Folio"

    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].next_by_code('banquet.reservation.folio')

    reservation_id = fields.Many2one('banquet.reservation', string='Reservation')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    pos_config_id = fields.Char(string='POS Config')
    name = fields.Char(string='Name', required=True,
                       default=_get_default_name,
                       track_visibility='onchange'
                       )
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    payment_date = fields.Date(string='Payment Date', default=fields.Date.context_today, required=True)
    payment_type = fields.Char(string='Payment Type')
    qty = fields.Integer(string='Qty')
    total_amount = fields.Monetary(string='Total Amount', required=True)
    paid_amount = fields.Monetary(string='Paid Amount', required=True)
    status_posting = fields.Char(string='Status Posting')
    status_payment = fields.Char(string='Status Payment')
    remark = fields.Char(string='Remark')
    is_residential = fields.Boolean(string='Is Residential', default=False)
    is_compliment = fields.Boolean(string='Is Compliment', default=False)
    is_include_tax = fields.Boolean(string='Is Include Tax', default=False)
    currency_id = fields.Many2one('res.currency', related='reservation_id.currency_id', readonly=True)

    @api.model
    @api.constrains('total_amount')
    def _check_amount(self):
        if self.total_amount < 0:
            raise ValidationError(_('Total amount cannot be negative.'))


class ReservationFolioLine(models.Model):
    _name = 'banquet.reservation.folio.line'
    _description = "Reservation Folio Line"

    folio_id = fields.Many2one('banquet.reservation.folio', string='Reservation Folio')
    pos_config_id = fields.Char(string='POS Config')
    reservation_rate_id = fields.Many2one('banquet.reservation.rate', string='Reservation Rate')
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict', index=True)
    qty = fields.Integer(string='Qty')
    price = fields.Monetary(string='Price', required=True)
    total_amount = fields.Monetary(string='Total Amount', required=True)
    description = fields.Char(string='Description')
    currency_id = fields.Many2one('res.currency', related='folio_id.currency_id', readonly=True)
