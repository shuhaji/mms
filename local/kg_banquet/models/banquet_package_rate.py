from odoo import models, fields


class BanquetPackageRate(models.Model):
    _name = 'banquet.package.rate'

    package_id = fields.Many2one('banquet.package')
    event_function_id = fields.Many2one('banquet.event.function', required=True)
    revenue_type = fields.Selection(selection=[('Food', 'Food'), ('Beverages', 'Beverages'),
                                               ('Other', 'Other'), ('Residential', 'Residential')], required=True)
    amount = fields.Integer(required=True)
