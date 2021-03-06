from odoo import api,fields,models,_


class KGPickingList(models.TransientModel):
    _name = 'table.picking.list'

    # salesperson_id = fields.Many2one('hr.employee', string='Salesperson', required=True)
    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)

    @api.multi
    def print_report(self):
        data = {
            # 'salesperson_id': self.salesperson_id,
            'start_date': self.start_date,
            'end_date': self.end_date,
        }
        return self.env.ref('kg_inventory.menu_kg_picking_list').report_action([], data=data)


