from odoo import models, fields, api


class EventMenu(models.Model):
    _name = 'banquet.event.menu'

    package_id = fields.Many2one('banquet.package', string='Package ID')
    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    menu_id = fields.Many2one('banquet.menu')
    event_function_id = fields.Many2one('banquet.event.function', string='Event Function')

    # TODO GET Name dari function_name + menu_name

    @api.onchange('menu_id', 'event_function_id')
    def onchange_menu_function(self):
        for rec in self:
            rec.name = "{event_function}-{event_menu}".format(
                event_function=rec.event_function_id.name if rec.event_function_id else "",
                event_menu=rec.menu_id.name if rec.menu_id else "")
