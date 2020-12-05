from odoo import models, fields, api
from odoo.exceptions import UserError

class BanquetPackage(models.Model):
    _name = 'banquet.package'

    name = fields.Char(string='Description')
    code = fields.Char(string='Code')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    tax_code = fields.Boolean(string='Tax')
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id.id)
    event_menu_ids = fields.One2many('banquet.event.menu', 'package_id', string='Event Menu')
    rate_ids = fields.One2many('banquet.package.rate', 'package_id', string='Event Menu')
    tax_ids = fields.Many2many('account.tax', 'banquet_package_taxes_rel', 'package_id', 'account_tax_id',
                               string="Taxes")
    currency_id = fields.Many2one('res.currency')
    remark = fields.Text(string='Remark')
    active = fields.Boolean(string='Active', default=1)
    additional_benefit = fields.Text(string='Additional Benefit')
    price_pax = fields.Integer(string='Price Per Person', compute='sum_rate_amount', store=True)
    isResidential = fields.Boolean(string='Residential', default=False)
    event_type_id = fields.Many2one('catalog.eventtype', string='Event Type')

    @api.depends('rate_ids')
    def sum_rate_amount(self):
        for rec in self:
            if rec.rate_ids:
                rec.price_pax = sum(rate.amount for rate in rec.rate_ids)
            else:
                rec.price_pax = 0

    @api.model
    def create(self, vals):
        res = super(BanquetPackage, self).create(vals)
        if not vals.get('rate_ids'):
            raise UserError("Revenue Distribution can not be empty")
        elif res.price_pax == 0:
            raise UserError("Price Per Person must be more than 0")
        return res

    @api.multi
    def write(self, vals):
        res = super(BanquetPackage, self).write(vals)
        if not self.rate_ids:
            raise UserError("Revenue Distribution can not be empty")
        elif self.price_pax == 0:
            raise UserError("Price Per Person must be more than 0")
        return res
