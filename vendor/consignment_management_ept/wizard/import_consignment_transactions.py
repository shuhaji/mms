from odoo import models, fields, api, _
import base64
from odoo.exceptions import Warning, ValidationError
from datetime import datetime
import xlrd
import xlwt
import xlsxwriter
import logging

_logger = logging.getLogger(__name__)


class import_consignment_transactions(models.TransientModel):
    _name = 'import.consignment.transactions'
    _description = 'Consignment Transactions Import Process'

    transaction_type = fields.Selection([
        ('transfer', 'Consignment Transfer'),
        ('return', 'Consignment Return'),
        ('order', 'Consignment Orders'),
        ('internal', 'Consignee to Consignee')], string='Transaction Type', default='transfer')
    choose_file = fields.Binary('Choose File')
    file_name = fields.Char('File Name')

    @api.multi
    def download_template(self):
        """ Download Template(Demo) File to see format
            @author : Priya Pal
            @last_updated_on : 29th Oct, 2018
        """
        try:
            if (self.transaction_type == 'transfer' or self.transaction_type == 'return'):
                attachment = self.env['ir.attachment'].search([('id', '=', self.env.ref(
                    'consignment_management_ept.ir_attachment_import_transfer_return_template_ept').id)])
            elif (self.transaction_type == 'order'):
                attachment = self.env['ir.attachment'].search([('id', '=', self.env.ref(
                    'consignment_management_ept.ir_attachment_import_order_template_ept').id)])
            elif (self.transaction_type == 'internal'):
                attachment = self.env['ir.attachment'].search([('id', '=', self.env.ref(
                    'consignment_management_ept.ir_attachment_import_internal_template_ept').id)])

            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % (attachment.id),
                'target': 'new',
                'nodestroy': False,
            }
        except Exception as e:
            _logger.error(e)
            raise Warning(
                "Hello %s, Something Went Wrong, Please try again or you should contact your Administrator" % (
                    self.env.user.name))

    @api.multi
    def do_import(self):
        ''' this is main method for import consignment transfer/return/internal/order
           @author : Priya Pal
           @last_updated_on : 27th Sept, 2018    
        '''
        if not self.choose_file:
            raise Warning("File Not Found To Import")
        if self.file_name and self.file_name[-3:] != 'xls' and self.file_name[-4:] != 'xlsx':
            raise Warning("Please Provide Only .xls OR .xlsx File to Import Consignment Transfer!!!")

        worksheet = self.get_worksheet(self.file_name, self.choose_file)
        self.validate_column_header(worksheet)

        data = self.get_data_from_file(worksheet)

        if self.transaction_type in ('transfer', 'return'):
            self.do_import_transfer_or_return(data)

        elif self.transaction_type == 'order':
            self.do_import_order(data)

        elif self.transaction_type == 'internal':
            self.do_import_internal(data)

        return {'effect': {'fadeout': 'slow',
                           'message': "Yeah %s, It's Done, You can check consignment logs for further details." % self.env.user.name,
                           'img_url': '/web/static/src/img/smile.svg', 'type': 'rainbow_man'}}

    @api.multi
    def get_worksheet(self, file_name, choose_file):
        """File read method.
           @author : Priya Pal
           @last_updated_on : 26th Sep, 2018
        """
        try:
            xl_workbook = xlrd.open_workbook(file_contents=base64.decodestring(choose_file))
            worksheet = xl_workbook.sheet_by_index(0)
        except Exception as e:
            error_value = str(e)
            raise ValidationError(error_value)
        return worksheet

    @api.multi
    def validate_column_header(self, worksheet):
        ''' Check transaction type and validate the column header as per selected file.
            @author : Priya Pal
            @last_updated_on : 26th Sep, 2018
        '''
        column_header = self.get_column_header(worksheet)

        if (self.transaction_type == 'transfer' or self.transaction_type == 'return'):
            require_fields = ['warehouse', 'consignee', 'product_sku', 'qty']
        elif (self.transaction_type == 'order'):
            require_fields = ['consignee', 'product_sku', 'qty']
        elif (self.transaction_type == 'internal'):
            require_fields = ['source_consignee', 'destination_consignee', 'product_sku', 'qty']

        if set(column_header.values()) == set(require_fields):
            return True
        else:
            raise Warning("Some of necessary columns are not found please refer template")

    @api.multi
    def get_column_header(self, worksheet):
        """Returns headers of uploaded file to import 
          @author : Priya Pal
          @last_updated_on : 26th Sep, 2018          
        """
        column_header = {}
        for col_index in range(worksheet.ncols):
            value = worksheet.cell(0, col_index).value.lower()
            column_header.update({col_index: value})
        return column_header

    @api.multi
    def get_data_from_file(self, worksheet):
        """extracts data from file to import, prepares dict and return the same
          @author : Priya Pal
          @last_updated_on : 26th Sep, 2018          
        """
        column_header = self.get_column_header(worksheet)
        try:
            data = []
            for row_index in range(1, worksheet.nrows):
                sheet_data = {}
                for col_index in range(worksheet.ncols):
                    if bool(worksheet.cell(row_index, col_index).value):
                        sheet_data.update({column_header.get(col_index): worksheet.cell(row_index, col_index).value})
                if bool(sheet_data):
                    data.append(sheet_data)
        except Exception as e:
            error_value = str(e)
            raise ValidationError(error_value)
        return data

    @api.multi
    def do_import_transfer_or_return(self, data):
        """ validate data, create done and pending log, creates transfer/return for done log as per transaction_type
            @author : Priya Pal
            @last_updated_on : 29th Oct, 2018         
        """
        try:
            # validate
            pending_log_lines_list, done_log_lines_list = self.validate_for_transfer_and_return(data)
            # create logs        
            done_log_id = self.create_transfer_or_return_logs(pending_log_lines_list, done_log_lines_list)
            # create transfer/return for done_log
            self.create_transfer_or_return(done_log_lines_list, done_log_id)

            return True

        except Exception as e:
            _logger.error(e)
            return False

    @api.multi
    def validate_for_transfer_and_return(self, data):
        """Validate  consignment transfer/return file data.
            @author : Priya Pal
            @last_updated_on : 29th Oct, 2018     
        """
        log_line_obj = self.env['consignment.log.line.ept']
        pending_log_lines_list = []
        done_log_lines_list = []
        line_no = 1
        try:
            for row in data:
                line_no += 1
                consignee_name = row.get('consignee')
                warehouse_name = row.get('warehouse')
                product_name = row.get('product_sku')
                qty = row.get('qty')
                msg = ""

                """
                    @goal : validate consignee data 
                """
                consignee = self.env['res.partner'].search([('name', '=', consignee_name)])
                if not consignee_name:
                    msg += "consignee name is missing.\n"
                elif not (consignee):
                    msg += "%s - No customer found with this name.\n" % consignee_name
                elif (len(consignee) > 1):
                    msg += "More then one customers with same name - %s exist.\n" % consignee_name
                elif not consignee.customer:
                    msg += '%s is not a Customer.\n' % consignee_name
                elif not consignee.is_consignee_customer:
                    msg += 'Customer %s is not a consignee.\n' % consignee_name

                """
                    @goal : validate warehouse data
                """
                warehouse = self.env['stock.warehouse'].search([('name', '=', warehouse_name)])
                if not warehouse_name:
                    msg += 'Warehouse name is missing.\n'
                elif not warehouse:
                    msg += '%s - No warehouse found of this name.\n' % warehouse_name
                elif warehouse.is_consignment_warehouse:
                    msg += '%s is a Consignment warehouse.\n' % warehouse_name

                """
                    @goal : validate quantity data
                """
                if int(qty) <= 0:
                    msg += 'Given qty is invalid.\n'

                """
                    @goal : validate product data
                """
                product = self.env['product.product'].search([('default_code', '=', product_name)])
                if not product_name:
                    msg += 'Product name is missing.\n'
                elif not product:
                    msg += '%s - No Product found of this sku(default_code).\n' % product_name
                elif product.type != 'product':
                    msg += '%s is not a Storable Product.\n' % product_name
                elif not product.is_consignment_product:
                    msg += 'Product of sku %s is not a consignment product.\n' % product_name

                """
                    @goal : add validate data to done_log_lines_list and 
                            incorrect data to pending_log_lines_list
                """
                if msg:
                    pending_log_lines_list.append({
                        'msg': msg,
                        'line_no': line_no,
                        'consignee': consignee_name,
                        'warehouse': warehouse_name,
                        'product': product_name,
                        'qty': qty
                    })
                else:
                    done_log_lines_list.append({
                        'msg': 'Successfully Done',
                        'line_no': line_no,
                        'consignee': consignee_name,
                        'warehouse': warehouse_name,
                        'product': product_name,
                        'qty': qty
                    })

            return pending_log_lines_list, done_log_lines_list

        except Exception as e:
            _logger.error(e)
            return False

    @api.multi
    def create_transfer_or_return_logs(self, pending_log_lines_list, done_log_lines_list):
        """create consignment logs and log lines with transaction type transfer/return and
           returns done_log_id
           @author : Priya Pal
           @last_updated_on : 29th Oct, 2018     
        """
        done_log_id = False
        dynamic = {'pending': pending_log_lines_list, 'done': done_log_lines_list}
        try:
            for state, list in dynamic.items():
                if list:
                    log_id = self.env['consignment.log.ept'].create({
                        'transaction_type': self.transaction_type,
                        'state': state
                    })
                    if state == 'done':
                        done_log_id = log_id

                    if state == 'pending' and list:
                        workbook = xlsxwriter.Workbook('pending_records.xlsx')
                        worksheet = workbook.add_worksheet()

                        worksheet.set_column('A:A', 22)
                        worksheet.set_column('B:B', 22)
                        worksheet.set_column('C:C', 22)
                        worksheet.set_column('D:D', 15)
                        worksheet.set_column('E:E', 50)

                        headers = ['consignee', 'warehouse', 'product_sku', 'qty', 'Message']
                        row = 0
                        col = 0
                        worksheet.write_row(row, col, headers)

                    vals = {
                        'name': self.file_name,
                        'datas': self.choose_file,
                        'datas_fname': self.file_name,
                        'type': 'binary',
                        'res_model': 'consignment.log.ept',
                        'res_id': log_id and log_id.id or False
                    }
                    self.env['ir.attachment'].create(vals)

                    for line in list:
                        if state == 'pending':
                            row += 1
                            worksheet.set_row(row, 40)

                            worksheet.write(row, 0, line.get("consignee") or '')
                            worksheet.write(row, 1, line.get("warehouse") or '')
                            worksheet.write(row, 2, line.get("product") or '')
                            worksheet.write(row, 3, line.get("qty") or 0)
                            worksheet.write(row, 4, line.get("msg") or '')

                        vals = {
                            'log_id': log_id.id,
                            'line_no': line.get("line_no"),
                            'consignee': line.get("consignee"),
                            'warehouse': line.get("warehouse"),
                            'product': line.get("product"),
                            'qty': line.get("qty"),
                            'msg': line.get("msg")
                        }
                        self.env['consignment.log.line.ept'].create(vals)
                    #                             log_line_data= self.env['consignment.log.line.ept'].create(vals)

                    if state == 'pending' and list:
                        workbook.close()
                        fp = open('pending_records.xlsx', 'rb')
                        fp.seek(0)
                        pending_data_file = base64.encodestring(fp.read())
                        fp.close()

                        vals = {
                            'name': 'pending_' + self.file_name,
                            'datas': pending_data_file,
                            'datas_fname': 'pending_' + self.file_name,
                            'type': 'binary',
                            'res_model': 'consignment.log.ept',
                            'res_id': log_id and log_id.id or False
                        }
                        self.env['ir.attachment'].create(vals)

            return done_log_id

        except Exception as e:
            _logger.error(e)
            return False

    @api.multi
    def create_transfer_or_return(self, done_log_lines_list, done_log_id):
        """create consignment transfer or return records
          @author : Priya Pal
          @last_updated_on : 29th Oct, 2018     
        """
        if done_log_lines_list:
            if self.transaction_type == 'transfer':
                consignee_loc = 'consignee_dest_id'
            elif self.transaction_type == 'return':
                consignee_loc = 'consignee_source_id'

            furnished_data = {}
            try:
                for dict in done_log_lines_list:
                    consignee = dict.get('consignee')
                    warehouse = dict.get('warehouse')
                    product = dict.get('product')
                    qty = dict.get('qty')

                    if consignee in furnished_data:
                        warehouse_records = furnished_data.get(consignee)
                        if warehouse in warehouse_records:
                            product_records = warehouse_records.get(warehouse)
                            if product in product_records:
                                existing_qty = product_records.get(product)
                                add_qty = existing_qty + qty
                                product_records.update({product: add_qty})
                            else:
                                product_records.update({product: qty})
                        else:
                            warehouse_records.update({warehouse: {product: qty}})
                    else:
                        furnished_data.update({consignee: {warehouse: {product: qty}}})

                for consignee, consignee_wise_data in furnished_data.items():
                    consignee_id = self.env['res.partner'].search([('name', '=', consignee)])
                    for warehouse, warehouse_wise_data in consignee_wise_data.items():
                        warehouse_id = self.env['stock.warehouse'].search([('name', '=', warehouse)])

                        transfer_id = self.env['consignment.process.ept'].create({
                            'consignment_type': self.transaction_type,
                            consignee_loc: consignee_id.id,
                            'warehouse_id': warehouse_id.id,
                            'consignment_log_id': done_log_id.id,
                            'origin': done_log_id.name
                        })

                        #                         line_list = []
                        for product, product_wise_data in warehouse_wise_data.items():
                            product_id = self.env['product.product'].search([('default_code', '=', product)])
                            qty = product_wise_data
                            vals = {
                                'consignment_process_id': transfer_id.id,
                                'product_id': product_id.id,
                                'quantity': qty
                            }
                            self.env['consignment.process.line.ept'].create(vals)
                        #                             line_list.append(vals)
                #
                #                         transfer_line_data= self.env['consignment.process.line.ept'].create(line_list)

                return True

            except Exception as e:
                _logger.error(e)
                return False

    @api.multi
    def do_import_order(self, data):
        """import consignment orders process
          @author : Priya Pal          
          @last_update_on : 29th Oct,2018         
        """
        try:
            # validate
            pending_log_lines_list, done_log_lines_list = self.validate_for_order(data)
            # create logs        
            done_log_id = self.create_order_logs(pending_log_lines_list, done_log_lines_list)
            # create consignment order for done_log
            self.create_order(done_log_lines_list, done_log_id)

            return True

        except Exception as e:
            _logger.error(e)
            return False

    @api.multi
    def validate_for_order(self, data):
        """Validate data for consignment order
           Returns : done_log_line_list for correct validated data and
                     pending_log_line_list for incorrect data with its msg
        @author : Priya Pal
        @last_updated_on : 29th Oct, 2018
        """
        pending_log_lines_list = []
        done_log_lines_list = []
        line_no = 1
        try:
            for row in data:
                line_no += 1
                source_partner = row.get('consignee')
                product_name = row.get('product_sku')
                qty = row.get('qty')
                msg = ""

                """
                    @goal : Validate source partner data
                """
                consignee = self.env['res.partner'].search([('name', '=', source_partner)])
                if not source_partner:
                    msg += " source consignee name is missing.\n"
                elif not (consignee):
                    msg += "%s - Customer not found of this name.\n" % source_partner
                elif (len(consignee) > 1):
                    msg += "More then one customers with same name - %s exist.\n" % source_partner
                elif not consignee.customer:
                    msg += '%s is not a customer.\n' % source_partner
                elif not consignee.is_consignee_customer:
                    msg += '%s Customer is not a consignee.\n' % source_partner

                """
                    @goal : Validate quantity data
                """
                if int(qty) <= 0:
                    msg += 'Given value for Qty is invalid.\n'

                """
                    @goal : Validate product data
                """
                product = self.env['product.product'].search([('default_code', '=', product_name)])
                if not product_name:
                    msg += 'Product name is missing.\n'
                elif not product:
                    msg += '%s - Product not found of this name.\n' % product_name
                elif product.type != 'product':
                    msg += '%s is not a Storable Product.\n' % product_name
                elif not product.is_consignment_product:
                    msg += 'Product - %s is not a consignment product.\n' % product_name

                """
                    @goal : add correct data to done_log_lines_list and 
                            incorrect data to pending_log_lines_list
                """
                if msg:
                    pending_log_lines_list.append(
                        {'msg': msg, 'line_no': line_no, 'consignee': source_partner, 'product': product_name,
                         'qty': qty})

                else:
                    done_log_lines_list.append(
                        {'msg': 'Successfully Done', 'line_no': line_no, 'consignee': source_partner,
                         'product': product_name, 'qty': qty})

            return pending_log_lines_list, done_log_lines_list

        except Exception as e:
            _logger.error(e)
            return False

    @api.multi
    def create_order_logs(self, pending_log_lines_list, done_log_lines_list):
        """create consignment order logs
          @author : Priya Pal
          @last_updated_on : 29th Oct, 2018                  
        """
        done_log_id = False
        dynamic = {'pending': pending_log_lines_list, 'done': done_log_lines_list}

        try:
            for state, list in dynamic.items():
                if list:
                    log_id = self.env['consignment.log.ept'].create({
                        'transaction_type': self.transaction_type,
                        'state': state
                    })
                    if state == 'done':
                        done_log_id = log_id

                    if state == 'pending' and list:
                        workbook = xlsxwriter.Workbook('pending_records.xlsx')
                        worksheet = workbook.add_worksheet()

                        worksheet.set_column('A:A', 22)
                        worksheet.set_column('B:B', 22)
                        worksheet.set_column('C:C', 22)
                        worksheet.set_column('D:D', 15)
                        worksheet.set_column('E:E', 50)

                        headers = ['consignee', 'product_sku', 'qty', 'Message']
                        row = 0
                        col = 0
                        worksheet.write_row(row, col, headers)

                    vals = {
                        'name': self.file_name,
                        'datas': self.choose_file,
                        'datas_fname': self.file_name,
                        'type': 'binary',
                        'res_model': 'consignment.log.ept',
                        'res_id': log_id and log_id.id or False
                    }
                    self.env['ir.attachment'].create(vals)

                    #                     line_list = []
                    for line in list:
                        if state == 'pending':
                            row += 1
                            worksheet.set_row(row, 40)

                            worksheet.write(row, 0, line.get("consignee") or '')
                            worksheet.write(row, 1, line.get("product") or '')
                            worksheet.write(row, 2, line.get("qty") or 0)
                            worksheet.write(row, 3, line.get("msg") or '')

                        vals = {
                            'log_id': log_id.id,
                            'line_no': line.get("line_no"),
                            'consignee': line.get("consignee"),
                            'product': line.get("product"),
                            'qty': line.get("qty"),
                            'msg': line.get("msg")
                        }
                        self.env['consignment.log.line.ept'].create(vals)
                    #                         line_list.append(vals)

                    #                     log_line_data= self.env['consignment.log.line.ept'].create(line_list)

                    if state == 'pending' and list:
                        workbook.close()
                        fp = open('pending_records.xlsx', 'rb')
                        fp.seek(0)
                        pending_data_file = base64.encodestring(fp.read())
                        fp.close()

                        vals = {
                            'name': 'pending_' + self.file_name,
                            'datas': pending_data_file,
                            'datas_fname': 'pending_' + self.file_name,
                            'type': 'binary',
                            'res_model': 'consignment.log.ept',
                            'res_id': log_id and log_id.id or False
                        }
                        self.env['ir.attachment'].create(vals)

            return done_log_id

        except Exception as e:
            _logger.error(e)
            return False

    @api.multi
    def create_order(self, done_log_lines_list, done_log_id):
        """create consignment sale order
            @author : Priya Pal
            @last_updated_on : 29th Oct, 2018         
        """
        furnished_data = {}
        try:
            for dict in done_log_lines_list:
                source_partner = dict.get('consignee')
                product = dict.get('product')
                qty = dict.get('qty')

                if source_partner in furnished_data:
                    product_records = furnished_data.get(source_partner)
                    if product in product_records:
                        existing_qty = product_records.get(product)
                        add_qty = existing_qty + qty
                        product_records.update({product: add_qty})
                    else:
                        product_records.update({product: qty})
                else:
                    furnished_data.update({source_partner: {product: qty}})

            for source_partner, source_partner_wise_data in furnished_data.items():
                source_partner_id = self.env['res.partner'].search([('name', '=', source_partner)])

                new_sale_order_record = self.env['sale.order'].new({
                    'partner_id': source_partner_id.id,
                    'state': 'draft',
                    'is_consignment_order': True,
                    'consignment_log_id': done_log_id.id,
                    'origin': done_log_id.name
                })
                new_sale_order_record.onchange_partner_shipping_id()
                new_sale_order_record.onchange_partner_id()
                new_sale_order_record.onchange_partner_id_warning()
                new_sale_order_record._onchange_warehouse_id()
                vals = new_sale_order_record._convert_to_write(new_sale_order_record._cache)

                order_id = self.env['sale.order'].create(vals)

                #                 line_list = []
                for product, product_wise_data in source_partner_wise_data.items():
                    product_id = self.env['product.product'].search([('default_code', '=', product)])
                    qty = product_wise_data

                    vals = {
                        'product_id': product_id.id,
                        'product_uom_qty': qty,
                        'order_id': order_id.id,
                        'product_uom': product_id.uom_id.id
                    }
                    new_sale_order_line_record = self.env['sale.order.line'].new(vals)
                    new_sale_order_line_record.product_id_change()
                    new_sale_order_line_record.product_uom_change()
                    new_sale_order_line_record._onchange_discount()

                    vals = new_sale_order_line_record._convert_to_write(new_sale_order_line_record._cache)
                    self.env['sale.order.line'].create(vals)

            #                     line_list.append(vals)
            #                 order_line_data= self.env['sale.order.line'].create(line_list)
            return True

        except Exception as e:
            _logger.error(e)
            return False

    @api.multi
    def do_import_internal(self, data):
        """import internal transfer, create consignee to consignee internal transfer.       
         @author : Priya Pal
         @last_updated_on : 29th Oct, 2018                 
        """
        try:
            # Validate Data
            pending_log_lines_list, done_log_lines_list = self.validate_for_internal(data)
            # create logs        
            done_log_id = self.create_internal_logs(pending_log_lines_list, done_log_lines_list)
            # create inter transfer as per done log list
            self.create_internal(done_log_lines_list, done_log_id)

            return True

        except Exception as e:
            _logger.error(e)
            return False

    @api.multi
    def validate_for_internal(self, data):
        """Validate data for internal transfer.
           Returns correct/validated data as done_log_list and
                incorrect/invalidated data as pending_log_list
          @author : Priya Pal
          @last_updated_on : 29th Oct, 2018
        """
        pending_log_lines_list = []
        done_log_lines_list = []
        line_no = 1
        try:
            for row in data:
                line_no += 1
                from_consignee = row.get('source_consignee')
                to_consignee = row.get('destination_consignee')
                product_name = row.get('product_sku')
                qty = row.get('qty')
                msg = ""

                """
                    @goal : Validation for source consignee 
                """
                consignee = self.env['res.partner'].search([('name', '=', from_consignee)])
                if not from_consignee:
                    msg += "Source Consignee name is missing.\n"
                elif not (consignee):
                    msg += "%s - No Customer found of this name.\n" % from_consignee
                elif (len(consignee) > 1):
                    msg += "More then one customers with same name - %s exist.\n" % from_consignee
                elif not consignee.customer:
                    msg += '%s is not a customer.\n' % from_consignee
                elif not consignee.is_consignee_customer:
                    msg += '%s Customer is not Consignee.\n' % from_consignee

                """
                    @goal : Validation for destination consignee 
                """
                dest_consignee = self.env['res.partner'].search([('name', '=', to_consignee)])
                if not to_consignee:
                    msg += "Destination Consignee name is missing.\n"
                elif not (dest_consignee):
                    msg += "%s - No Customer found of this name.\n" % to_consignee
                elif (len(dest_consignee) > 1):
                    msg += "More then one customers with same name - %s exist.\n" % to_consignee
                elif not dest_consignee.customer:
                    msg += '%s is not a customer.\n' % to_consignee
                elif not dest_consignee.is_consignee_customer:
                    msg += '%s Customer is not Consignee.\n' % to_consignee

                if from_consignee == to_consignee:
                    msg += 'Source and Destination consignee should not be the same.\n'

                """
                    @goal : Validation for quantity 
                """
                if int(qty) <= 0:
                    msg += 'Given Qty is invalid.\n'

                """
                    @goal : Validation for product 
                """
                product = self.env['product.product'].search([('default_code', '=', product_name)])
                if not product_name:
                    msg += 'Product name is missing.\n'
                elif not product:
                    msg += '%s - Product not found of this sku.\n' % product_name
                elif product.type != 'product':
                    msg += '%s is not a Storable Product.\n' % product_name
                elif not product.is_consignment_product:
                    msg += '%s is not a consignment product.\n' % product_name

                """
                    @goal : append validated data to done_log_list and
                                 invalidated data to pending_log_list
                """
                if msg:
                    pending_log_lines_list.append({
                        'msg': msg,
                        'line_no': line_no,
                        'consignee': from_consignee,
                        'dest_consignee': to_consignee,
                        'product': product_name,
                        'qty': qty
                    })

                else:
                    done_log_lines_list.append({
                        'msg': 'Successfully Done',
                        'line_no': line_no,
                        'consignee': from_consignee,
                        'dest_consignee': to_consignee,
                        'product': product_name,
                        'qty': qty
                    })

            return pending_log_lines_list, done_log_lines_list

        except Exception as e:
            _logger.error(e)
            return False

    @api.multi
    def create_internal_logs(self, pending_log_lines_list, done_log_lines_list):
        """create logs while importing consignee to consignee internal transfer       
         @author : Priya Pal
         @last_updated_on: 29 th Oct,2018                    
        """
        done_log_id = False
        dynamic = {'pending': pending_log_lines_list, 'done': done_log_lines_list}
        try:
            for state, list in dynamic.items():
                if list:
                    log_id = self.env['consignment.log.ept'].create({
                        'transaction_type': self.transaction_type,
                        'state': state
                    })
                    if state == 'done':
                        done_log_id = log_id

                    if state == 'pending' and list:
                        workbook = xlsxwriter.Workbook('pending_records.xlsx')
                        worksheet = workbook.add_worksheet()

                        worksheet.set_column('A:A', 22)
                        worksheet.set_column('B:B', 22)
                        worksheet.set_column('C:C', 22)
                        worksheet.set_column('D:D', 15)
                        worksheet.set_column('E:E', 50)

                        headers = ['source_consignee', 'destination_consignee', 'product_sku', 'qty', 'Message']
                        row = 0
                        col = 0
                        worksheet.write_row(row, col, headers)

                    vals = {
                        'name': self.file_name,
                        'datas': self.choose_file,
                        'datas_fname': self.file_name,
                        'type': 'binary',
                        'res_model': 'consignment.log.ept',
                        'res_id': log_id and log_id.id or False
                    }
                    self.env['ir.attachment'].create(vals)

                    #                     line_list = []
                    for line in list:
                        if state == 'pending':
                            row += 1
                            worksheet.set_row(row, 40)

                            worksheet.write(row, 0, line.get("consignee") or '')
                            worksheet.write(row, 1, line.get("dest_consignee") or '')
                            worksheet.write(row, 2, line.get("product") or '')
                            worksheet.write(row, 3, line.get("qty") or 0)
                            worksheet.write(row, 4, line.get("msg") or '')

                        vals = {
                            'log_id': log_id.id,
                            'line_no': line.get("line_no"),
                            'source_consignee': line.get("consignee"),
                            'destination_consignee': line.get("dest_consignee"),
                            'product': line.get("product"),
                            'qty': line.get("qty"),
                            'msg': line.get("msg")
                        }
                        self.env['consignment.log.line.ept'].create(vals)
                    #                         line_list.append(vals)
                    #                     self.env['consignment.log.line.ept'].create(line_list)

                    if state == 'pending' and list:
                        workbook.close()
                        fp = open('pending_records.xlsx', 'rb')
                        fp.seek(0)
                        pending_data_file = base64.encodestring(fp.read())
                        fp.close()

                        vals = {
                            'name': 'pending_' + self.file_name,
                            'datas': pending_data_file,
                            'datas_fname': 'pending_' + self.file_name,
                            'type': 'binary',
                            'res_model': 'consignment.log.ept',
                            'res_id': log_id and log_id.id or False
                        }
                        self.env['ir.attachment'].create(vals)
            return done_log_id

        except Exception as e:
            _logger.error(e)
            return False

    @api.multi
    def create_internal(self, done_log_lines_list, done_log_id):
        """create/import consignee to consignee internal transfer         
         @author : Priya Pal
         @last_updated_on : 29th Oct, 2018                   
        """
        furnished_data = {}
        try:
            for dict in done_log_lines_list:
                source_consignee = dict.get('consignee')
                dest_consignee = dict.get('dest_consignee')
                product = dict.get('product')
                qty = dict.get('qty')

                if source_consignee in furnished_data:
                    dest_consignee_records = furnished_data.get(source_consignee)
                    if dest_consignee in dest_consignee_records:
                        product_records = dest_consignee_records.get(dest_consignee)
                        if product in product_records:
                            existing_qty = product_records.get(product)
                            add_qty = existing_qty + qty
                            product_records.update({product: add_qty})
                        else:
                            product_records.update({product: qty})
                    else:
                        dest_consignee_records.update({dest_consignee: {product: qty}})
                else:
                    furnished_data.update({source_consignee: {dest_consignee: {product: qty}}})

            for source_consignee, source_consignee_wise_data in furnished_data.items():
                source_consignee_id = self.env['res.partner'].search([('name', '=', source_consignee)])
                for dest_consignee, dest_consignee_wise_data in source_consignee_wise_data.items():
                    dest_consignee_id = self.env['res.partner'].search([('name', '=', dest_consignee)])
                    transfer_id = self.env['consignment.process.ept'].create({
                        'consignment_type': self.transaction_type,
                        'consignee_source_id': source_consignee_id.id,
                        'consignee_dest_id': dest_consignee_id.id,
                        'consignment_log_id': done_log_id.id,
                        'origin': done_log_id.name
                    })

                    #                     line_list = []
                    for product, product_wise_data in dest_consignee_wise_data.items():
                        product_id = self.env['product.product'].search([('default_code', '=', product)])
                        qty = product_wise_data
                        vals = {
                            'consignment_process_id': transfer_id.id,
                            'product_id': product_id.id,
                            'quantity': qty
                        }
                        self.env['consignment.process.line.ept'].create(vals)
            #                         line_list.append(vals)

            #                     self.env['consignment.process.line.ept'].create(line_list)
            return True

        except Exception as e:
            _logger.error(e)
            return False
