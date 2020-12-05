from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ReservationRate(models.Model):
    _name = 'banquet.reservation.rate'
    _inherit = ['mail.thread']
    _description = "Reservation Rate"

    reservation_id = fields.Many2one('banquet.reservation', string='Reservation')
    company_id = fields.Many2one(comodel_name='res.company', string='Company',
                                 required=True, default=lambda self: self.env.user.company_id.id,
                                 )
    package_id = fields.Many2one('banquet.package', string='Package', required=True, track_visibility='onchange')
    reservation_folio_id = fields.Many2one('banquet.reservation.folio', string='Reservation Folio')
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict', index=True)
    name = fields.Text(track_visibility='onchange')
    date = fields.Date(default=fields.Date.context_today, required=True, track_visibility='onchange')
    attendance = fields.Integer(default=1, required=True, track_visibility='onchange')
    price = fields.Monetary(string='Price Per Person', store=True, track_visibility='onchange')
    amount = fields.Monetary(compute='_compute_amounts', store=True)
    amount_before_tax = fields.Monetary(compute='_compute_amounts', store=True)
    tax_amount = fields.Float(digits=0, compute='_compute_amounts', store=True)
    amendment = fields.Boolean(default=False)
    is_residential = fields.Boolean(default=False, string='Residential')
    description = fields.Char()
    currency_id = fields.Many2one('res.currency', related='reservation_id.currency_id', readonly=True)
    tax_ids = fields.Many2many('account.tax', string='Taxes', store=True)
    tax_ids_after_fiscal_position = fields.Many2many('account.tax',
                                                     compute='_get_tax_ids_after_fiscal_position',
                                                     string='Taxes')

    @api.model
    @api.constrains('amount')
    def _check_amount(self):
        if self.amount < 0:
            raise ValidationError(_('The amount cannot be negative.'))

    @api.onchange('package_id')
    def _onchange_package_id(self):
        self.tax_ids = [(6, 0, self.package_id.tax_ids.ids)] #.package_id.tax_ids.ids
        self.price = self.package_id.price_pax

    @api.onchange('is_residential')
    def _onchange_clear_value(self):
        self.package_id = None

    @api.multi
    @api.depends('package_id')
    def _get_tax_ids_after_fiscal_position(self):
        for line in self:
            line.tax_ids_after_fiscal_position = line.reservation_id.fiscal_position_id.map_tax(
                line.tax_ids,
                line.product_id,
                line.reservation_id.partner_id)

    @api.depends('price', 'attendance')
    def _compute_amounts(self):
        for line in self:
            fpos = line.reservation_id.fiscal_position_id
            tax_ids_after_fiscal_position = fpos.map_tax(
                line.tax_ids, line.product_id) if fpos else line.tax_ids

            price = line.price
            taxes = tax_ids_after_fiscal_position.compute_all(
                price, line.reservation_id.currency_id, line.attendance,
                product=None, partner=None)

            subtotal = taxes['total_included']

            line.update({
                'amount': subtotal,
                'amount_before_tax': taxes['total_excluded'],
                'tax_amount': subtotal - taxes['total_excluded'],
            })
