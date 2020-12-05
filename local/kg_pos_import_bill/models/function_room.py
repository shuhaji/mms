# -*- coding: utf-8 -*-

from odoo import models, api, fields, _
from odoo.exceptions import except_orm, Warning, RedirectWarning, UserError


class FunctionRoom(models.Model):
    _name = 'function.room.type'
    _description = u'function_room'

    # _rec_name = 'name'
    _order = 'code ASC'

    code = fields.Char("Functional Room Code", required=True)
    name = fields.Char("Description Room")

