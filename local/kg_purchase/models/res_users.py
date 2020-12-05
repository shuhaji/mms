
from odoo import fields, models, api


class KGResUsers(models.Model):
    _inherit = 'res.users'

    # TODO : cegah 1 user multiemployee
