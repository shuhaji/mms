from odoo import models, fields, api, _


class stock_warehouse_ept(models.Model):
    _inherit = 'stock.warehouse'

    is_consignment_warehouse = fields.Boolean('Consignment Warehouse', default=False)
