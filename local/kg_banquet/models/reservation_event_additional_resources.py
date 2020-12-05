from odoo import models, fields, api


class EventAdditionalResources(models.Model):
    _name = 'banquet.reservation.event.additional.resources'
    _inherit = ['mail.thread']
    _description = "Event Additional Resources"

    reservation_event_id = fields.Many2one('banquet.reservation.event')
    reservation_id = fields.Many2one(related='reservation_event_id.reservation_id')

    item_type = fields.Selection([
        ('fnb', 'Food & Beverage'),
        ('eqp', 'Equipment'),
        ('svc', 'Service'),
    ], 'Type', track_visibility='onchange')
    product_id = fields.Many2one('product.product',
                                 'Product', track_visibility='onchange')
    qty = fields.Integer(string='Quantity', track_visibility='onchange')
    price = fields.Integer(string='Price', track_visibility='onchange')
    description = fields.Char(string='Remark')

    # amendment information -- start
    # amd_state = fields.Char(string='Amendment State', track_visibility='onchange')
    is_in_amendment = fields.Boolean(related='reservation_event_id.is_in_amendment')
    # we need to store amendment no here also, for filtering purpose in reports
    amendment_no = fields.Integer(string="Amendment No", default=0, track_visibility='always', )
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

        result = super(EventAdditionalResources, self).write(values)
        return result

    @api.onchange('reservation_event_id')
    def onchange_reservation_event_id(self):
        if not self._origin.reservation_event_id and self.reservation_event_id:
            self.amendment_no = self.reservation_id.last_amendment_no
