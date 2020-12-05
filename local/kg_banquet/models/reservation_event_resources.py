from odoo import models, fields, api


class EventResources(models.Model):
    _name = 'banquet.reservation.event.resources'
    _inherit = ['mail.thread']
    _description = "Event Resources"

    reservation_event_id = fields.Many2one('banquet.reservation.event')
    reservation_id = fields.Many2one(related='reservation_event_id.reservation_id')

    menu_id = fields.Many2one('banquet.menu',
                              'Menu', required=True)
    product_ids = fields.Many2many(
        'product.product', 'product_menu_res_event_rel', 'product_id',
        'event_id', 'Products')

    qty = fields.Integer(string='Quantity', track_visibility='onchange')
    remark = fields.Char()

    # amendment information -- start
    # amd_state = fields.Char(string='Amendment State', track_visibility='onchange')
    is_in_amendment = fields.Boolean(related='reservation_event_id.is_in_amendment')
    # we need to store amendment no here also, for filtering purpose in reports
    amendment_no = fields.Integer(string="Amendment No", default=0, track_visibility='always',)
    pivot_amd_no = fields.Integer(string="Pivot Amendment No", default=0, track_visibility='onchange')
    old_qty = fields.Integer(string='Old Quantity', default=0)
    # amendment information -- end

    @api.multi
    def write(self, values):
        if self.is_in_amendment:
            pivot_amd_no = values.get('pivot_amd_no', self.pivot_amd_no)
            amendment_no = values.get('amendment_no', self.amendment_no)
            if pivot_amd_no != amendment_no and (
                (values.get('qty') and values.get('qty', '') != self.old_qty)
            ):
                # update old values
                values['pivot_amd_no'] = amendment_no
                values['old_qty'] = self.qty

        result = super(EventResources, self).write(values)
        return result

    @api.onchange('reservation_event_id')
    def onchange_reservation_event_id(self):
        if not self._origin.reservation_event_id and self.reservation_event_id:
            self.amendment_no = self.reservation_id.last_amendment_no

    @api.onchange('menu_id')
    def _get_default_product(self):
        self.product_ids = self.menu_id.product_ids
