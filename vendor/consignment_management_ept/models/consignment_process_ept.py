from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError


class consignment_process_ept(models.Model):
    _name = 'consignment.process.ept'
    _description = 'Consignment Processes'
    _order = "date desc, name desc, id desc"

    name = fields.Char(default='New')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    consignee_source_id = fields.Many2one('res.partner', string='From Consignee')
    consignee_dest_id = fields.Many2one('res.partner', string='To Consignee')
    date = fields.Datetime(' Date', default=fields.Datetime.now)
    consignment_process_line_ids = fields.One2many('consignment.process.line.ept', 'consignment_process_id',
                                                   string='Product Lines', copy=True)
    stock_picking_ids = fields.One2many('stock.picking', 'consignment_process_id', string="Delivery")
    pickings_count = fields.Integer(string='Delivery Orders', compute='_compute_picking_ids')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('processed', 'Processed'),
        ('delivered', 'Delivered'),
        ('cancel', 'Cancelled'),
    ], string='Status', copy=False, default='draft')
    consignment_type = fields.Selection([
        ('transfer', 'Consignment Transfer'),
        ('return', 'Consignment Return'),
        ('internal', 'Consignee to Consignee')], string='Consignment Type')
    consignment_log_id = fields.Many2one('consignment.log.ept', string="Consignment Log")
    origin = fields.Char(string="Source")

    @api.onchange('consignee_source_id')
    def onchange_consignee_source_id(self):
        ''' This method set consignee destination based on consignee source
            it means both field value are not same
            @author : Dhaval Sanghani
        '''
        if self.consignment_type == 'internal' and self.consignee_source_id:
            return {'domain': {
                'consignee_dest_id': [('id', '!=', self.consignee_source_id.id), ('is_consignee_customer', '=', True)]}}

    @api.model
    def create(self, vals):
        ''' This will create new records of consignment process
            @author : Dhaval Sanghani
            @param : includes required data to create records
            @return : it will return record_id created by method
        '''
        if vals.get('consignment_type') == 'transfer':
            vals['name'] = self.env.ref('consignment_management_ept.seq_consignment_process').next_by_id() or 'New'

        if vals.get('consignment_type') == 'return':
            vals['name'] = self.env.ref('consignment_management_ept.seq_consignment_return').next_by_id() or 'New'

        if vals.get('consignment_type') == 'internal':
            vals['name'] = self.env.ref('consignment_management_ept.seq_consignment_internal').next_by_id() or 'New'

        result = super(consignment_process_ept, self).create(vals)

        return result

    @api.depends('stock_picking_ids')
    def _compute_picking_ids(self):
        ''' it will compute total count of stock picking for consignment transfer,consignment return
            @author : Dhaval Sanghani
            @return: total delivery order
        '''
        for order in self:
            order.pickings_count = len(order.stock_picking_ids)

    @api.multi
    def action_view_delivery(self):
        ''' This function returns an action that display existing delivery orders
            of given consignment transfer order ids. It can either be a in a list or in a form
            view, if there is only one delivery order to show.
            @author : Dhaval Sanghani
            @return: list view / form view
        '''
        action = self.env.ref('stock.action_picking_tree_all').read()[0]

        pickings = self.mapped('stock_picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action

    @api.multi
    def validate_products(self):
        ''' It will check that product and quantity is given or not
            @author : Dhaval Sanghani
        '''
        flag = 0
        for item in self.consignment_process_line_ids:
            if item.product_id and item.quantity > 0.0:
                flag = 1
            else:
                flag = 0

        if flag > 0:
            return True

        else:
            raise Warning("Please Provide Valid Product and Quantity!!!")
            return False

    @api.multi
    def prepare_stock_picking_vals(self):
        ''' this method used for prepare vals for create record of stock picking
            @author : Dhaval Sanghani
            @return : values for create record
        '''
        new_picking_record = self.env['stock.picking'].new({
                                                               'picking_type_id': self.warehouse_id.int_type_id.id or self.consignee_source_id.consignment_location_id.get_warehouse().int_type_id.id,
                                                               'origin': self.name})
        new_picking_record.onchange_picking_type()

        if self.consignment_type == 'transfer':
            new_picking_record.update({'partner_id': self.consignee_dest_id.id})
            new_picking_record.location_id = self.warehouse_id.lot_stock_id.id
            new_picking_record.location_dest_id = self.consignee_dest_id.consignment_location_id.id

        if self.consignment_type == 'return':
            new_picking_record.update({'partner_id': self.consignee_source_id.id})
            new_picking_record.location_id = self.consignee_source_id.consignment_location_id.id
            new_picking_record.location_dest_id = self.warehouse_id.lot_stock_id.id

        if self.consignment_type == 'internal':
            new_picking_record.update({'partner_id': self.consignee_source_id.id})
            new_picking_record.location_id = self.consignee_source_id.consignment_location_id.id
            new_picking_record.location_dest_id = self.consignee_dest_id.consignment_location_id.id

        new_picking_record.consignment_process_id = self.id
        vals = new_picking_record._convert_to_write(new_picking_record._cache)
        return vals

    @api.multi
    def prepare_stock_move_vals(self, picking_id, vals):
        ''' this method prepare vals for stock move for every product
            @author : Dhaval Sanghani
            @return: values for create record
        '''
        new_record = self.env['stock.move'].new(vals)
        new_record.onchange_product_id()
        new_record.onchange_product_uom()
        '''
            remaining method to call
            #d1 = {'product_id':line.product_id.id,'product_uom':line.product_id.uom_id.id,'product_qty':line.quantity,'date':self.date}
            #values = new_record.onchange(d1,self.consignee_dest_id.id,new_record.onchange_quantity())
        '''
        new_record.onchange_date()
        new_record.picking_id = picking_id
        new_record.product_uom_qty = vals['product_qty']
        new_record.date_expected = str(self.date)

        if self.consignment_type == 'transfer':
            new_record.location_id = self.warehouse_id.lot_stock_id.id
            new_record.location_dest_id = self.consignee_dest_id.consignment_location_id.id

        if self.consignment_type == 'return':
            new_record.location_id = self.consignee_source_id.consignment_location_id.id
            new_record.location_dest_id = self.warehouse_id.lot_stock_id.id

        if self.consignment_type == 'internal':
            new_record.location_id = self.consignee_source_id.consignment_location_id.id
            new_record.location_dest_id = self.consignee_dest_id.consignment_location_id.id

        vals = new_record._convert_to_write(new_record._cache)
        return vals

    @api.multi
    def do_consignment_process(self):
        ''' It is main method for consignment process
            @author : Dhaval Sanghani
        '''
        result = self.validate_products()

        if result:
            picking_vals = self.prepare_stock_picking_vals()
            picking_id = self.env['stock.picking'].create(picking_vals)

            if picking_id:
                self.write({'state': 'processed'})
                stock_move_ids = []
                for line in self.consignment_process_line_ids:
                    vals = {'product_id': line.product_id.id, 'picking_type_id': picking_id.picking_type_id.id or False,
                            'product_uom': line.product_id.uom_id.id, 'product_qty': line.quantity,
                            'date': str(self.date)}
                    move_vals = self.prepare_stock_move_vals(picking_id, vals)
                    stock_move_ids.append(self.env['stock.move'].create(move_vals))
                if (self.state, '=', 'processed'):
                    picking_id.action_confirm()
                    picking_id.action_assign()

    @api.multi
    def unlink(self):
        ''' If consignment processed and delivery already done , then user can not delete consignment record,
            and then it raise the warning.
            @author : Priya Pal
            @lastUpdate : 22-10-2018
        '''
        for order in self:
            if order.state not in ('draft', 'cancel'):
                raise Warning(_('In order to delete a Consignment, you must cancel it first.'))
        return super(consignment_process_ept, self).unlink()

    @api.multi
    def cancel_consignment_process(self):
        ''' it will change the state to cancel of stock picking and stock move
            @author : Dhaval Sanghani
        '''
        self.mapped('stock_picking_ids').action_cancel()
        return self.write({'state': 'cancel'})

    @api.multi
    def set_to_draft(self):
        ''' it will change the state to draft
            @author : Dhaval Sanghani
        '''
        return self.write({'state': 'draft'})


class consignment_process_line_ept(models.Model):
    _name = 'consignment.process.line.ept'
    _description = 'Consignment Process Lines'

    consignment_process_id = fields.Many2one('consignment.process.ept', string='Consignment No')
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float('Quantity', default='1')
