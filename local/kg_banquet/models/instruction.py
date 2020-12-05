from odoo import models, fields


class KGBanquetInstruction(models.Model):
    _name = 'banquet.instruction'
    # _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Banquet Instruction"

    department_id = fields.Many2one('hr.department', 'Department', required=True)
    name = fields.Char(string='Name', required=True)
