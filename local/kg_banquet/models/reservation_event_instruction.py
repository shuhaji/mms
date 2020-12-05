from odoo import models, fields, api


class EventInstruction(models.Model):
    _name = 'banquet.reservation.event.instruction'
    _inherit = ['mail.thread']
    _description = "Event Instruction"

    reservation_event_id = fields.Many2one('banquet.reservation.event')
    reservation_id = fields.Many2one(related='reservation_event_id.reservation_id')

    description = fields.Char(string="Description/Remark", track_visibility='onchange')
    department_id = fields.Many2one('hr.department', 'Responsible Department', required=True
                                    , track_visibility='onchange')
    instruction_id = fields.Many2one('banquet.instruction', 'Instruction', required=True
                                     , track_visibility='onchange')
    start_time = fields.Char(string='Start Time', track_visibility='onchange', default='00:00')
    end_time = fields.Char(string='End Time', track_visibility='onchange', default='00:00')

    # amendment information -- start
    # amd_state = fields.Char(string='Amendment State', track_visibility='onchange')
    is_in_amendment = fields.Boolean(related='reservation_event_id.is_in_amendment')
    # we need to store amendment no here also, for filtering purpose in reports
    amendment_no = fields.Integer(string="Amendment No", default=0, track_visibility='always', )
    # pivot_amd_no = fields.Integer(string="Pivot Amendment No", default=0, track_visibility='onchange')
    # amendment information -- end

    @api.multi
    def write(self, values):
        # if self.is_in_amendment:
        #     pivot_amd_no = values.get('pivot_amd_no', self.pivot_amd_no)
        #     amendment_no = values.get('amendment_no', self.amendment_no)
        #     if pivot_amd_no != amendment_no and (
        #             (values.get('qty') and values.get('qty', '') != self.old_qty)
        #     ):
        #         # update old values
        #         values['pivot_amd_no'] = amendment_no
        #         values['old_qty'] = self.qty
        result = super(EventInstruction, self).write(values)
        return result

    @api.onchange('reservation_event_id')
    def onchange_reservation_event_id(self):
        if not self._origin.reservation_event_id and self.reservation_event_id:
            self.amendment_no = self.reservation_id.last_amendment_no

    @api.onchange('reservation_event_id', 'start_time', 'end_time')
    def onchange_date(self):
        self.start_time = self.reservation_event_id.start_time
        self.end_time = self.reservation_event_id.end_time


