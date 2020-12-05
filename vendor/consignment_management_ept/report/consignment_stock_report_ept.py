from odoo import models, fields, api, _

try:
    import xlwt
    from xlwt import Borders
except ImportError:
    xlwt = None
import base64
from io import BytesIO
from datetime import datetime


class consignment_stock_report_ept(models.TransientModel):
    _name = 'consignment.stock.report.ept'
    _description = 'Consignment Report'

    @api.model
    def _starting_date_of_current_month(self):
        """ Returns starting date of ongoing month
        @author : Er.Vaidehi Vasani
        @last_updated_on : 5th Sep, 2018 
        """
        today = fields.date.today()
        year = today.year
        month = today.month
        day = 1
        starting_date_of_current_month = fields.date(year, month, day)
        return starting_date_of_current_month

    from_date = fields.Date('From Date', default=_starting_date_of_current_month)
    to_date = fields.Date('To Date', default=fields.date.today())
    report_type = fields.Selection([
        ('product_wise', 'Product Wise'),
        ('consignee_wise', 'Consignee Wise')
    ], default="consignee_wise")
    report_as = fields.Selection([
        ('onscreen', 'View On-Screen'),
        ('pdf', 'Download PDF Report'),
        ('xls', 'Download XLS Report')
    ], default="onscreen")
    consignee_ids = fields.Many2many('res.partner', string='Consignees')
    product_ids = fields.Many2many('product.product', string='Products')
    datas = fields.Binary('File')
    ignore_non_moving_records = fields.Boolean(string="Ignore Non Moving Records", default=True)

    #     @api.onchange('report_type')
    #     def onchange_report_type(self):
    #         """ domain for product_ids
    #         @author : Er.Vaidehi Vasani
    #         @last_updated_on : 7th Sep, 2018
    #         """
    #         if self.report_type == 'product_wise':
    #             consignment_template = self.env['product.product'].search([('is_consignment_product', '=', True)]).mapped('product_tmpl_id')
    #             if len(consignment_template) == 1:
    #                 domain = [('id', 'in', consignment_template.id), ('type', '=', 'product')]
    #             else:
    #                 domain = [('id', 'in', consignment_template.ids), ('type', '=', 'product')]
    #             return {'domain' : {'product_ids':domain}}

    @api.multi
    def retrive_data(self):
        """ Retrives consignment information for report
        @author : Er.Vaidehi Vasani
        @last_updated_on : 5th Sep, 2018 
        """
        from_date = self.from_date
        to_date = self.to_date

        if self.report_type == 'consignee_wise':
            if self.consignee_ids:
                consignee_or_product_ids = self.consignee_ids.ids or [0]
                consignee_or_product_ids_str = '(' + str(self.consignee_ids.ids or [0]).strip('[]') + ')'
            else:
                all_consignee = self.env['res.partner'].search([('is_consignee_customer', '=', True)])
                consignee_or_product_ids = all_consignee.ids or [0]
                consignee_or_product_ids_str = '(' + str(all_consignee.ids or [0]).strip('[]') + ')'

        elif self.report_type == 'product_wise':
            if self.product_ids:
                consignee_or_product_ids = self.product_ids.ids or [0]
                consignee_or_product_ids_str = '(' + str(self.product_ids.ids or [0]).strip('[]') + ')'
            else:
                all_product = self.env['product.product'].search([('is_consignment_product', '=', True)])
                consignee_or_product_ids = all_product.ids or [0]
                consignee_or_product_ids_str = '(' + str(all_product.ids or [0]).strip('[]') + ')'

        qry = """
                
            DROP TABLE IF EXISTS consignment_stock_table;
            
            CREATE TEMPORARY TABLE consignment_stock_table(
                    date_done DATE,
                    consignee INT,
                    product INT,
                    transfer_qty INT,
                    received_from_another INT,
                    return_qty INT,
                    transfer_to_another INT,
                    ordered_qty INT
                );

            INSERT INTO consignment_stock_table
                SELECT
                    date_done,
                    consignee,
                    product,
                    sum(transfer_qty) as transfer_qty,
                    sum(received_from_another) as received_from_another,
                    sum(return_qty) as return_qty,
                    sum(transfer_to_another) as transfer_to_another,
                    sum(ordered_qty) as ordered_qty
                FROM
                    (SELECT
                        sp.date_done,
                        cpe.consignee_dest_id as consignee,
                        sm.product_id as product,
                        sum(sm.product_uom_qty) as transfer_qty,
                        0 as return_qty,
                        0 as ordered_qty,
                        0 as received_from_another,
                        0 as transfer_to_another 
                        
                        FROM stock_picking sp
                             left join stock_move sm on sp.id = sm.picking_id
                             inner join consignment_process_ept cpe on cpe.id = sp.consignment_process_id
            
                        WHERE cpe.consignment_type = 'transfer' AND
                              sm.state = 'done' AND
                              CASE when '%s' = 'consignee_wise' THEN cpe.consignee_dest_id 
                                                                ELSE sm.product_id 
                                                                END 
                                                                     in %s AND
                              sp.date_done :: date  <= '%s'
              
                        GROUP BY consignee, product, date_done

                    UNION ALL
            
                    SELECT
                        sp.date_done,
                        cpe.consignee_source_id as consignee,
                        sm.product_id as product,
                        0 as transfer_qty,
                        sum(sm.product_uom_qty) as return_qty,
                        0 as ordered_qty,
                        0 as received_from_another,
                        0 as transfer_to_another  
        
                        FROM stock_picking sp
                             left join stock_move sm on sp.id = sm.picking_id
                             inner join consignment_process_ept cpe on cpe.id = sp.consignment_process_id
            
                        WHERE cpe.consignment_type = 'return' AND 
                              sm.state = 'done' AND
                              CASE when '%s' = 'consignee_wise' THEN cpe.consignee_source_id  
                                                                ELSE sm.product_id 
                                                                END 
                                                                     in %s AND 
                              sp.date_done :: date  <= '%s'
                          
                        GROUP BY consignee, product, date_done
        
                    UNION ALL
    
                    SELECT
                        sp.date_done,
                        so.partner_id as consignee,
                        sm.product_id as product,
                        0 as transfer_qty,
                        0 as return_qty,
                        sum(sm.product_uom_qty) as ordered_qty,
                        0 as received_from_another,
                        0 as transfer_to_another  
    
                        FROM stock_picking sp 
                             left join stock_move sm on sp.id = sm.picking_id
                             inner join sale_order so on sp.sale_id = so.id 
            
                        WHERE so.is_consignment_order = True AND 
                              sm.state = 'done' AND
                              CASE when '%s' = 'consignee_wise' THEN so.partner_id 
                                                                ELSE sm.product_id 
                                                                END 
                                                                     in %s AND
                              sp.date_done :: date  <= '%s'
                          
                        GROUP BY consignee, product, date_done

                    UNION ALL

                    SELECT
                        sp.date_done,
                        cpe.consignee_dest_id as consignee,
                        sm.product_id as product,
                        0 as transfer_qty,
                        0 as return_qty,
                        0 as ordered_qty,
                        sum(sm.product_uom_qty) as received_from_another,
                        0 as transfer_to_another 
                        
                        FROM stock_picking sp
                             left join stock_move sm on sp.id = sm.picking_id
                             inner join consignment_process_ept cpe on cpe.id = sp.consignment_process_id
        
                        WHERE cpe.consignment_type = 'internal' AND
                              sm.state = 'done' AND 
                              CASE when '%s' = 'consignee_wise' THEN cpe.consignee_dest_id
                                                                ELSE sm.product_id 
                                                                END 
                                                                     in %s AND
                              sp.date_done :: date  <= '%s'
                          
                        GROUP BY consignee, product, date_done

                    UNION ALL

                    SELECT 
                        sp.date_done,
                        cpe.consignee_source_id as consignee,
                        sm.product_id as product,
                        0 as transfer_qty,
                        0 as return_qty,
                        0 as ordered_qty,
                        0 as received_from_another,
                        sum(sm.product_uom_qty) as transfer_to_another 
                        
                        FROM stock_picking sp
                             left join stock_move sm on sp.id = sm.picking_id
                             inner join consignment_process_ept cpe on cpe.id = sp.consignment_process_id
    
                        WHERE cpe.consignment_type = 'internal' AND 
                              sm.state = 'done' AND
                              CASE when '%s' = 'consignee_wise' THEN cpe.consignee_source_id 
                                                                ELSE sm.product_id 
                                                                END 
                                                                     in %s AND
                              sp.date_done :: date  <= '%s'
                          
                        GROUP BY consignee, product, date_done
                
                    )all_data
                GROUP BY consignee, product, date_done;


    
            SELECT 
                consignee,
                product,
                sum(opening_qty) as opening_qty,
                sum(transfer_qty) as transfer_qty,
                sum(received_from_another) as received_from_another,
                sum(return_qty) as return_qty,
                sum(transfer_to_another) as transfer_to_another,
                sum(ordered_qty) as ordered_qty,
                  sum(opening_qty) + sum(transfer_qty) + sum(received_from_another)
                - sum(return_qty) - sum(transfer_to_another) - sum(ordered_qty) as closing_qty
            FROM
                (SELECT 
                    consignee,
                    product,
                    sum(transfer_qty) - sum(return_qty) - sum(ordered_qty) + sum(received_from_another) - sum(transfer_to_another) as opening_qty,
                    0 as transfer_qty,
                    0 as return_qty,
                    0 as ordered_qty,
                    0 as received_from_another,
                    0 as transfer_to_another  
                
                    FROM consignment_stock_table
                    WHERE date_done < '%s'
                    GROUP BY consignee, product

                UNION ALL

                SELECT 
                    consignee,
                    product,
                    0 as opening_qty,
                    sum(transfer_qty) as transfer_qty,
                    sum(return_qty) as return_qty,
                    sum(ordered_qty) as ordered_qty,
                    sum(received_from_another) as received_from_another,
                    sum(transfer_to_another) as transfer_to_another

                    FROM consignment_stock_table
                    WHERE date_done >= '%s'
                    GROUP BY consignee, product
                )temp2

            GROUP BY consignee, product
        
        """ % (
            self.report_type, consignee_or_product_ids_str, to_date,
            self.report_type, consignee_or_product_ids_str, to_date,
            self.report_type, consignee_or_product_ids_str, to_date,
            self.report_type, consignee_or_product_ids_str, to_date,
            self.report_type, consignee_or_product_ids_str, to_date,

            from_date, from_date
        )
        #         print(qry)
        self._cr.execute(qry)
        result = self._cr.dictfetchall()

        if not result:
            return False

        furnished_result = {}
        if self.report_type == 'product_wise':
            focus = 'product'
        elif self.report_type == 'consignee_wise':
            focus = 'consignee'

        for dict in result:
            key = dict.get(focus)
            dict.pop(focus)
            if key in furnished_result.keys():
                list = furnished_result.get(key)
                list.append(dict)
            else:
                furnished_result.update({key: [dict]})

        if not self.ignore_non_moving_records:
            for remaining_consignee_or_product in (consignee_or_product_ids - furnished_result.keys()):
                furnished_result.update({remaining_consignee_or_product: []})

        return furnished_result

    @api.multi
    def get_report(self):
        """ calls appropriate method to generate different report - pdf/xls/onscreen...
        @author : Er.Vaidehi Vasani
        @last_updated_on : 21st Sep, 2018 
        """
        if not self.from_date <= self.to_date:
            return {'effect': {'fadeout': 'slow', 'message': "Hey %s, Date range is invalid." % self.env.user.name,
                               'img_url': '/web/static/src/img/warning.png', 'type': 'rainbow_man'}}

        if self.report_as == 'onscreen':
            return self.onscreen_report()
        elif self.report_as == 'pdf':
            return self.generate_pdf_report()
        elif self.report_as == 'xls':
            return self.generate_excel_report()

    @api.multi
    def generate_excel_report(self):
        """ Prints Consignment Xlsx Report
        @author : Er.Vaidehi Vasani
        @last_updated_on : 6th Sep, 2018 
        """
        workbook = xlwt.Workbook()

        header = xlwt.easyxf(
            "font: bold on, height 200; pattern:pattern solid, fore_colour gray25; alignment: horiz center ,vert center ")
        left_align = xlwt.easyxf(
            "font: height 200; alignment: horiz left, vert center; pattern: pattern solid, fore_colour gray25")
        right_align = xlwt.easyxf(
            "font: height 200; alignment: horiz right, vert center; pattern: pattern solid, fore_colour gray25")

        xlwt.add_palette_colour("blue", 0x21)
        workbook.set_colour_RGB(0x21, 176, 216, 230)
        blue_format = xlwt.easyxf(
            "font: height 200,bold on, name Arial; alignment: horiz center, vert center;  pattern: pattern solid, fore_colour blue;  borders: top thin,right thin,bottom thin,left thin")

        xlwt.add_palette_colour("pink", 0x17)
        workbook.set_colour_RGB(0x17, 255, 204, 204)
        pink_format = xlwt.easyxf(
            "font: height 200,bold on, name Arial; alignment: horiz center, vert center;  pattern: pattern solid, fore_colour pink;  borders: top thin,right thin,bottom thin,left thin")

        result = self.retrive_data()

        if not result:
            return {'effect': {'fadeout': 'slow',
                               'message': "Hey %s, No Data Found To Generate Report." % self.env.user.name,
                               'img_url': '/web/static/src/img/warning.png', 'type': 'rainbow_man'}}

        for key, values in result.items():
            if self.report_type == 'consignee_wise':
                key_name = self.env['res.partner'].browse(key).consignment_location_name
                consignee_name = self.env['res.partner'].browse(key).name
            elif self.report_type == 'product_wise':
                key_name = product_name = self.env['product.product'].browse(key).display_name

            worksheet = workbook.add_sheet(str(key_name))

            worksheet.col(0).width = 7000
            worksheet.col(1).width = 3000
            worksheet.col(2).width = 3000
            worksheet.col(3).width = 8000
            worksheet.col(4).width = 3000
            worksheet.col(5).width = 7000
            worksheet.col(6).width = 3000
            worksheet.col(7).width = 3000

            worksheet.write_merge(0, 1, 0, 7, 'Consignment Stock Report', header)
            worksheet.write_merge(2, 2, 0, 3, str(self.from_date), left_align)
            worksheet.write_merge(2, 2, 4, 7, str(self.to_date), right_align)
            if self.report_type == 'consignee_wise':
                worksheet.write_merge(3, 4, 0, 7, consignee_name, pink_format)
            elif self.report_type == 'product_wise':
                worksheet.write_merge(3, 4, 0, 7, product_name, pink_format)

            if self.report_type == 'consignee_wise':
                worksheet.write(5, 0, 'Product', blue_format)
            elif self.report_type == 'product_wise':
                worksheet.write(5, 0, 'Consignee(Location)', blue_format)
            worksheet.write(5, 1, 'Opening Qty', blue_format)
            worksheet.write(5, 2, 'Transfer Qty', blue_format)
            worksheet.write(5, 3, 'Received From Another Consignee', blue_format)
            worksheet.write(5, 4, 'Return Qty', blue_format)
            worksheet.write(5, 5, 'Transfer To Another Consignee', blue_format)
            worksheet.write(5, 6, 'Order Qty', blue_format)
            worksheet.write(5, 7, 'Closing Qty', blue_format)

            row = 6

            for record in values:
                if self.report_type == 'consignee_wise':
                    product = self.env['product.product'].browse(record.get('product')).display_name
                    worksheet.write(row, 0, product or '')
                elif self.report_type == 'product_wise':
                    consignee = self.env['res.partner'].browse(record.get('consignee'))
                    name = consignee.name
                    loc = consignee.consignment_location_name
                    display_consignee = name + '(' + loc + ')'
                    worksheet.write(row, 0, display_consignee or '')

                worksheet.write(row, 1, record.get('opening_qty', 0))
                worksheet.write(row, 2, record.get('transfer_qty', 0))
                worksheet.write(row, 3, record.get('received_from_another', 0))
                worksheet.write(row, 4, record.get('return_qty', 0))
                worksheet.write(row, 5, record.get('transfer_to_another', 0))
                worksheet.write(row, 6, record.get('ordered_qty', 0))
                worksheet.write(row, 7, record.get('closing_qty', 0))
                row = row + 1

        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        file = base64.encodestring(fp.read())
        fp.close()
        self.write({'datas': file})
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=consignment.stock.report.ept&download=true&field=datas&id=%s&filename= Consignment Report - %s.xls' % (
            self.id, datetime.now().strftime("%Y-%m-%d")),
            'target': 'new',
        }

    @api.multi
    def generate_pdf_report(self):
        """ Prints Consignment PDF Report
        @author : Er.Vaidehi Vasani
        @last_updated_on : 5th Sep, 2018 
        """
        return self.env.ref('consignment_management_ept.action_consignment_stock_report').report_action(self)

    @api.multi
    def onscreen_report(self):
        """ On-Screen Report through pivot view 
        @author : Er.Vaidehi Vasani
        @last_updated_on : 18th Sep, 2018 
        """
        result = self.retrive_data()

        if not result:
            return {'effect': {'fadeout': 'slow',
                               'message': "Hey %s, No Data Found To Generate Report." % self.env.user.name,
                               'img_url': '/web/static/src/img/warning.png', 'type': 'rainbow_man'}}

        report_records = self.env['consignment.onscreen.report']
        action = self.env.ref('consignment_management_ept.action_onscreen_report')
        report = action.read()[0]

        tree_view = self.env.ref('consignment_management_ept.view_onscreen_consignment_report_tree_view', False)
        if self.report_type == 'consignee_wise':
            pivot_view = self.env.ref(
                'consignment_management_ept.view_onscreen_consignment_report_consignee_wise_pivot', False)
        elif self.report_type == 'product_wise':
            pivot_view = self.env.ref('consignment_management_ept.view_onscreen_consignment_report_product_wise_pivot',
                                      False)

        report['views'] = [(tree_view and tree_view.id or False, 'tree'),
                           (pivot_view and pivot_view.id or False, 'pivot')]

        if self.report_type == 'consignee_wise':
            for consignee, records in result.items():
                for record in records:
                    report_records += self.env['consignment.onscreen.report'].create({
                        'consignee': self.env['res.partner'].browse(consignee).name + '(' +
                                     self.env['res.partner'].browse(consignee).consignment_location_name + ')',
                        'product_id': record.get('product'),
                        'opening_qty': record.get('opening_qty'),
                        'transfer_qty': record.get('transfer_qty'),
                        'received_from_another': record.get('received_from_another'),
                        'return_qty': record.get('return_qty'),
                        'transfer_to_another': record.get('transfer_to_another'),
                        'order_qty': record.get('ordered_qty'),
                        'closing_qty': record.get('closing_qty'),
                    })
            report['context'] = {'group_by': 'consignee'}

        elif self.report_type == 'product_wise':
            for product, records in result.items():
                for record in records:
                    report_records += self.env['consignment.onscreen.report'].create({
                        'product_id': product,
                        'consignee': self.env['res.partner'].browse(record.get('consignee')).name + '(' +
                                     self.env['res.partner'].browse(
                                         record.get('consignee')).consignment_location_name + ')',
                        'opening_qty': record.get('opening_qty'),
                        'transfer_qty': record.get('transfer_qty'),
                        'received_from_another': record.get('received_from_another'),
                        'return_qty': record.get('return_qty'),
                        'transfer_to_another': record.get('transfer_to_another'),
                        'order_qty': record.get('ordered_qty'),
                        'closing_qty': record.get('closing_qty'),
                    })
            report['context'] = {'group_by': 'product_id'}

        if len(report_records) == 1:
            report['domain'] = "[('id','=',%s)]" % (report_records.id)
        else:
            report['domain'] = "[('id','in',%s)]" % (report_records.ids)

        return report


class consignment_onscreen_report(models.TransientModel):
    _name = 'consignment.onscreen.report'
    _description = 'Consignment OnScreen Report'

    consignee = fields.Char('Consignee(Location)')
    product_id = fields.Many2one('product.product', 'Product')
    opening_qty = fields.Float('Opening Qty')
    transfer_qty = fields.Float('Transfer Qty')
    received_from_another = fields.Float('Received From Another Consignee')
    return_qty = fields.Float('Return Qty')
    transfer_to_another = fields.Float('Transfer To Another Consignee')
    order_qty = fields.Float('Order Qty')
    closing_qty = fields.Float('Closing Qty')
