
from odoo import models, fields, api


class KGPurchaseType(models.Model):
    _name = 'purchase.type'

    code = fields.Char('Code', required=True)
    name = fields.Char('Name', required=True)
