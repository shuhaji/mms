from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError
from datetime import datetime, timedelta
import time
import logging

_logger = logging.getLogger(__name__)


class consignment_log_ept(models.Model):
    _name = 'consignment.log.ept'
    _description = 'Consignment Logs'
    _order = "date desc, name desc, id desc"

    @api.multi
    def _compute_created_transactions(self):
        ''' Count number of records according to transaction_type
            @author : Priya Pal                     
            @last_updated_on : 29th Oct, 2018
        '''
        for record in self:
            try:
                if record.transaction_type == 'order':
                    record.transaction_count = len(record.order_ids)
                elif record.transaction_type in ['return', 'internal', 'transfer']:
                    record.transaction_count = len(record.transaction_ids)
            except Exception as e:
                _logger.error(e)
                return False

    name = fields.Char(default='New')
    date = fields.Datetime(' Date', default=fields.Datetime.now)
    log_line_ids = fields.One2many('consignment.log.line.ept', 'log_id', string='Log Lines')
    state = fields.Selection([
        ('pending', 'Pending '),
        ('done', 'Done'),
    ], string='Status', copy=False, default='pending')
    transaction_type = fields.Selection([
        ('transfer', 'Consignment Transfer'),
        ('return', 'Consignment Return'),
        ('order', 'Consignment Orders'),
        ('internal', 'Consignee to Consignee')], string='Transaction Type')
    transaction_ids = fields.One2many('consignment.process.ept', 'consignment_log_id', string="Transactions")
    order_ids = fields.One2many('sale.order', 'consignment_log_id', string="Orders")
    transaction_count = fields.Integer(compute='_compute_created_transactions', string="Transactions Imported")

    @api.multi
    def view_consignment_transactions(self):
        ''' returns imported consignment transfer/return/order/internal as per transaction_type.
        @author : Priya Pal                     
        @last_updated_on : 29th Oct, 2018
        '''
        try:
            if self.transaction_type == 'order':
                action = self.env.ref('sale.action_orders')
            elif self.transaction_type == 'transfer':
                action = self.env.ref('consignment_management_ept.action_menu_consignment_transfer')
            elif self.transaction_type == 'return':
                action = self.env.ref('consignment_management_ept.action_menu_consignment_return')
            elif self.transaction_type == 'internal':
                action = self.env.ref('consignment_management_ept.action_menu_consignee_to_consignee_transfer')

            result = action.read()[0]

            if self.transaction_type == 'order':
                if len(self.order_ids) > 1:
                    result['domain'] = "[('id','in',%s)]" % self.order_ids.ids
                else:
                    result['domain'] = "[('id','=',%s)]" % self.order_ids.id
            else:
                if len(self.transaction_ids) > 1:
                    result['domain'] = "[('id','in',%s)]" % self.transaction_ids.ids
                else:
                    result['domain'] = "[('id','=',%s)]" % self.transaction_ids.id

            if self.transaction_type == 'order':
                tree_view = self.env.ref('sale.sale.view_quotation_tree_with_onboarding', False)
                form_view = self.env.ref('sale.sale.view_order_form', False)
            elif self.transaction_type == 'transfer':
                tree_view = self.env.ref('consignment_management_ept.tree_view_consignment_transfer_ept', False)
                form_view = self.env.ref('consignment_management_ept.form_view_consignment_transfer_ept', False)
            elif self.transaction_type == 'return':
                tree_view = self.env.ref('consignment_management_ept.tree_view_consignment_transfer_return_ept', False)
                form_view = self.env.ref('consignment_management_ept.form_view_consignment_transfer_return_ept', False)
            elif self.transaction_type == 'internal':
                tree_view = self.env.ref('consignment_management_ept.tree_view_consignment_internal_ept', False)
                form_view = self.env.ref('consignment_management_ept.form_view_consignment_internal_ep', False)

            result['views'] = [(tree_view and tree_view.id or False, 'tree'),
                               (form_view and form_view.id or False, 'form')]

            return result

        except Exception as e:
            _logger.error(e)
            return False

    @api.model
    def create(self, vals):
        ''' set name through sequence while creating log record
            @author : Priya Pal
            @last_updated_on : 27th Sep, 2018 
        '''
        vals['name'] = self.env.ref('consignment_management_ept.seq_consignment_log').next_by_id() or 'New'
        result = super(consignment_log_ept, self).create(vals)
        return result


class consignment_log_line_ept(models.Model):
    _name = 'consignment.log.line.ept'
    _description = 'Consignment Log Lines'

    log_id = fields.Many2one('consignment.log.ept', string='Log_Id')
    line_no = fields.Float('Line No in xls')
    consignee = fields.Char('Consignee')
    warehouse = fields.Char('Warehouse')
    source_consignee = fields.Char('Source Consignee')
    destination_consignee = fields.Char('Destination Consignee')
    product = fields.Char('Product')
    qty = fields.Char('Qty')
    msg = fields.Char(string='Message')
