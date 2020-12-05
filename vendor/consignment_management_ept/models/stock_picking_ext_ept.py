from odoo import models, fields, api, _


class stock_picking_ids_ept(models.Model):
    _inherit = 'stock.picking'

    consignment_process_id = fields.Many2one('consignment.process.ept', string='Consignment Transaction Ref')

    @api.multi
    def action_done(self):
        for record in self:
            if record.consignment_process_id:
                res = super(stock_picking_ids_ept, record).action_done()
                if record.state == 'done':
                    record.consignment_process_id.write({
                        'state': 'delivered'
                    })
            else:
                super(stock_picking_ids_ept, record).action_done()
