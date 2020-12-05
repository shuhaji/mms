from odoo import api, fields, models, _


class ContractTaxType(models.Model):
    _inherit = "hr.contract"

    tax_type = fields.Selection([('gross', 'Gross'), ('gross_up', 'Gross Up'), ('nett', 'Nett')], 'Tax Type',
                                default='gross_up')
    accommodation = fields.Integer('Accommodation')
    transportation = fields.Integer('Transportation')
    mobile = fields.Integer('Mobile')
    food = fields.Integer('Food')
    nature = fields.Integer('Nature Of Work')
    position = fields.Integer('Position')
