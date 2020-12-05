from odoo import models, fields, api
from odoo.exceptions import UserError


class IrActionsReport(models.Model):
    """ Inherit from ir.actions.report to allow customizing the template
    file. The user cam chose a template from a list.
    The list is configurable in the configuration tab, see py3o_template.py
    """

    _inherit = 'ir.actions.report'

    report_type = fields.Selection(
        selection_add=[("mrt", "KG Report (mrt)")]
        )
