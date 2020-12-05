from odoo import models, fields, api, _
from odoo.exceptions import Warning


class res_partner_ept(models.Model):
    _inherit = 'res.partner'

    consignment_location_id = fields.Many2one('stock.location', string='Consignment Location')
    consignment_route_id = fields.Many2one('stock.location.route', string='Consignment Route')
    is_consignee_customer = fields.Boolean('Consignee', default=False)
    consignment_location_name = fields.Char('Location Name')

    @api.onchange('is_consignee_customer')
    def onchange_is_consignee_customer(self):
        '''set consignment location name if it is blank 
           @author : Er. Vaidehi Vasani, Emipro Technologies Pvt Ltd
           @last_updated_on : 3rd Nov, 2018
        '''
        if self.is_consignee_customer and not self.consignment_location_name:
            self.consignment_location_name = self.name or ''

    @api.multi
    def _create_consignee_location(self, location_name):
        '''It will Find existing Consignee Location, if found it will return otherwise it will create new location
           @author : Dhaval Sanghani
           @param : Consignment Location Name
           @return : Location Id
        '''
        location_obj = self.env['stock.location']
        view_location_id = self.env['stock.warehouse'].search(
            [('is_consignment_warehouse', '=', 1)]).view_location_id.id
        location_id = location_obj.with_context(active_test=False).search(
            [('location_id', '=', view_location_id), ('name', '=', location_name)])
        if location_id:
            return location_id

        else:
            loc_id = location_obj.create({'name': location_name, 'location_id': view_location_id})
            return loc_id

    @api.multi
    def _prepare_procurement_vals(self, consignee_location_id, consignee_location_name):
        ''' It will prepare vals for create procurement rule
            @author : Dhaval Sanghani
            @param: Consignee Location Id and Consignment Location Name
            @return: Prepare Vals
        '''
        warehouse_id = self.env['stock.warehouse'].search(
            [('view_location_id', '=', consignee_location_id.location_id.id)])
        location_id = self.env['stock.location'].search([('usage', '=', 'customer')])[0]
        pull_ids_data = []
        pull_ids_vals = {
            'name': 'Consignee: ' + consignee_location_name + ' -> Customer',
            'action': 'move',
            'location_src_id': consignee_location_id.id,
            'picking_type_id': warehouse_id.out_type_id.id,
            'location_id': location_id.id,
            'warehouse_id': warehouse_id.id

        }
        #         rule_ids_data.append((0,0,rule_ids_vals))
        pull_ids_data.append((0, 0, pull_ids_vals))
        return pull_ids_data

    @api.multi
    def _create_consignee_route(self, consignee_location_id, consignee_location_name):
        ''' This Method will Find Consignee Route, If found then return otherwise create it
            @author : Dhaval Sanghani
            @param: Consignee Location Id and Consignment Location Name
            @return: Consignee Route Id
        '''
        location_route_obj = self.env['stock.location.route']
        route_id = location_route_obj.with_context(active_test=False).search(
            [('name', '=', consignee_location_name + ' || Ship Only')])

        if route_id:
            return route_id

        else:
            #             rule_ids_vals = self._prepare_procurement_vals(consignee_location_id,consignee_location_name)
            pull_ids_vals = self._prepare_procurement_vals(consignee_location_id, consignee_location_name)
            vals = {
                'name': consignee_location_name + ' || Ship Only',
                'sale_selectable': True,
                'product_selectable': False,
                #                 'rule_ids' : rule_ids_vals,
                'pull_ids': pull_ids_vals
            }
            return location_route_obj.create(vals)

    @api.constrains('consignment_location_name')
    def _check_consignee_location_name(self):
        ''' This constrain check that Consignment Location name is unique
            @author : Dhaval Sanghani
            @return : True / False 
        '''
        name = self.search(
            [('consignment_location_name', '=ilike', self.consignment_location_name), ('id', '!=', self.id)])

        if name:
            raise Warning('Error!..Location name already exists..please provide Unique Location Name')
        else:
            return True

    @api.model
    def create(self, vals):
        ''' This is main create method. It will create a Consignee
            @author : Dhaval Sanghani
            @param: vals that is entered from frontend
            @return: new Consignee Record Id
        '''
        if vals.get('is_consignee_customer') == True:
            if vals.get('consignment_location_name') == False:
                vals.update({'consignment_location_name': vals['name']})
            consignee_location_id = self._create_consignee_location(vals['consignment_location_name'])
            route_id = self._create_consignee_route(consignee_location_id, vals['consignment_location_name'])
            vals.update({'consignment_location_id': consignee_location_id.id})
            vals.update({'consignment_route_id': route_id.id})
        return super(res_partner_ept, self).create(vals)

    @api.multi
    def write(self, vals):
        ''' This is write method. It will update existing record
            @author : Dhaval Sanghani
            @param: vals that is entered from frontend
            @return: existing record id
        '''
        new_name = vals.get('consignment_location_name')
        locations_to_update = self.env['stock.location']
        routes_to_update = self.env['stock.location.route']
        #         rule_ids_update = self.env['stock.rule']
        pull_ids_update = self.env['procurement.rule']

        if 'consignment_location_name' in vals:
            locations_to_update = self.mapped('consignment_location_id')
            routes_to_update = self.mapped('consignment_route_id')
            #             rule_ids_update  = routes_to_update.with_context(active_test=False).rule_ids
            pull_ids_update = routes_to_update.with_context(active_test=False).pull_ids

            if not locations_to_update or not routes_to_update or not pull_ids_update:
                if not locations_to_update:
                    location_id = self._create_consignee_location(new_name)
                    vals.update({'consignment_location_id': location_id.id})
                    locations_to_update = location_id

                if not routes_to_update:
                    route_id = self._create_consignee_route(locations_to_update, new_name)
                    vals.update({'consignment_route_id': route_id})
                    routes_to_update = route_id

        if 'is_consignee_customer' in vals:
            if vals['is_consignee_customer'] == False:
                self.consignment_location_id.write({'active': False})
                self.consignment_route_id.pull_ids.write({'active': False})
                self.consignment_route_id.write({'active': False})

            else:

                if self.consignment_location_id and self.consignment_route_id:
                    self.consignment_location_id.write({'active': True})
                    self.consignment_route_id.write({'active': True})
                    self.consignment_route_id.with_context(active_test=False).pull_ids.write({'active': True})

                if not self.consignment_location_id:
                    location_id = self._create_consignee_location(new_name)
                    vals.update({'consignment_location_id': location_id.id})
                    location_id.write({'active': True})

                if not self.consignment_route_id:
                    route_id = self._create_consignee_route(location_id, new_name)
                    vals.update({'consignment_route_id': route_id.id})
                    route_id.write({'active': True})
                    route_id.with_context(active_test=False).pull_ids.write({'active': True})

        result = super(res_partner_ept, self).write(vals)

        if result and locations_to_update and routes_to_update:
            locations_to_update.write({'name': new_name})
            routes_to_update.write({'name': new_name + ' || Ship Only'})
            pull_ids_update.write({'name': 'Consignee: ' + new_name + ' -> Customer'})
