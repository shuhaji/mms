from odoo import models, fields, api, _


class sale_order_ept(models.Model):
    _inherit = 'sale.order'

    is_consignment_order = fields.Boolean('Consignment Order', default=False)
    consignment_log_id = fields.Many2one('consignment.log.ept', string="Consignment Log")

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        ''' This method set warehouse id when customer is consignee and is_consignment_order is true
            @author : Dhaval Sanghani
        '''
        result = super(sale_order_ept, self).onchange_partner_id()

        if self.state == 'draft':
            if self.is_consignment_order == True:

                domain = {'partner_id': [('is_consignee_customer', '=', True)]}

                if self.partner_id:
                    if self.partner_id.is_consignee_customer == True:
                        self.warehouse_id = self.partner_id.consignment_location_id.location_id.get_warehouse().id

                if self.order_line:
                    for line in self.order_line:
                        if not line.route_id == self.partner_id.consignment_route_id:
                            line.route_id = self.partner_id.consignment_route_id.id

                result = {'domain': domain}
        return result


class sale_order_line_ept(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def product_id_change(self):
        ''' This method set route id when customer is consignee and is_consignment_order is true
            @author : Dhaval Sanghani
        '''
        result = super(sale_order_line_ept, self).product_id_change()

        if self.order_id.is_consignment_order == True:
            domain = {'product_id': [('is_consignment_product', '=', True)]}
            result = {'domain': domain}
        if self.order_id:
            if self.order_id.partner_id:
                if self.product_id:
                    if self.order_id.is_consignment_order == True:
                        if self.order_id.partner_id.is_consignee_customer == True:
                            if self.order_id.partner_id.consignment_route_id:
                                self.route_id = self.order_id.partner_id.consignment_route_id.id

        return result
