from odoo.api import Environment, SUPERUSER_ID
from . import models
from . import wizard
from . import report


def create_default_warehouse(cr, registry):
    env = Environment(cr, SUPERUSER_ID, {})
    vals = {'name': 'Consignment', 'code': 'CON', 'is_consignment_warehouse': 1}
    consignment_warehouse = env['stock.warehouse'].search([('code', '=', vals['code'])])
    if not consignment_warehouse:
        env['stock.warehouse'].create(vals)
    else:
        consignment_warehouse.write({'is_consignment_warehouse': True})
