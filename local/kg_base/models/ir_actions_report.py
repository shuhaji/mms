# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools.safe_eval import safe_eval
from odoo.tools.misc import find_in_path
from odoo.tools import config
from odoo.sql_db import TestCursor
from odoo.http import request

import time
import base64
import io
import logging
import os
import lxml.html
import tempfile
import subprocess
import re

from lxml import etree
from contextlib import closing
from distutils.version import LooseVersion
from reportlab.graphics.barcode import createBarcodeDrawing
from PyPDF2 import PdfFileWriter, PdfFileReader


_logger = logging.getLogger(__name__)


class KGIrActionsReport(models.Model):
    _inherit = 'ir.actions.report'
    
    @api.multi
    def render_qweb_pdf(self, res_ids=None, data=None):
        # In case of test environment without enough workers to perform calls to wkhtmltopdf,
        # fallback to render_html.
        
        # custom code by andi
        if res_ids:
            Model = self.env[self.model]
            record_ids = Model.browse(res_ids)
            if Model._name == 'account.invoice':
                for record in record_ids:
                    current_user = self.env['res.users'].browse(self.env.context.get('uid', False))
                    if current_user:
                        if not current_user.has_group('kg_account.group_invoice_duplicate_report_access_rights'):
                            if record.print_counter > 0:
                                raise ValidationError(_('Invoice is already printed and you do not have access to reprint the invoice again!'))

                    if not record.print_via_button:
                        record.increase_print_counter()
                        # record.print_counter += 1

                    record.print_via_button = False
        # end of custom code

        if tools.config['test_enable'] and not tools.config['test_report_directory']:
            return self.render_qweb_html(res_ids, data=data)

        # As the assets are generated during the same transaction as the rendering of the
        # templates calling them, there is a scenario where the assets are unreachable: when
        # you make a request to read the assets while the transaction creating them is not done.
        # Indeed, when you make an asset request, the controller has to read the `ir.attachment`
        # table.
        # This scenario happens when you want to print a PDF report for the first time, as the
        # assets are not in cache and must be generated. To workaround this issue, we manually
        # commit the writes in the `ir.attachment` table. It is done thanks to a key in the context.
        context = dict(self.env.context)
        if not config['test_enable']:
            context['commit_assetsbundle'] = True

        # Disable the debug mode in the PDF rendering in order to not split the assets bundle
        # into separated files to load. This is done because of an issue in wkhtmltopdf
        # failing to load the CSS/Javascript resources in time.
        # Without this, the header/footer of the reports randomly disapear
        # because the resources files are not loaded in time.
        # https://github.com/wkhtmltopdf/wkhtmltopdf/issues/2083
        context['debug'] = False

        # The test cursor prevents the use of another environnment while the current
        # transaction is not finished, leading to a deadlock when the report requests
        # an asset bundle during the execution of test scenarios. In this case, return
        # the html version.
        if isinstance(self.env.cr, TestCursor):
            return self.with_context(context).render_qweb_html(res_ids, data=data)[0]

        save_in_attachment = {}
        if res_ids:
            # Dispatch the records by ones having an attachment and ones requesting a call to
            # wkhtmltopdf.
            Model = self.env[self.model]
            record_ids = Model.browse(res_ids)
            wk_record_ids = Model
            if self.attachment:
                for record_id in record_ids:
                    attachment_id = self.retrieve_attachment(record_id)
                    if attachment_id:
                        save_in_attachment[record_id.id] = attachment_id
                    if not self.attachment_use or not attachment_id:
                        wk_record_ids += record_id
            else:
                wk_record_ids = record_ids
            res_ids = wk_record_ids.ids

        # A call to wkhtmltopdf is mandatory in 2 cases:
        # - The report is not linked to a record.
        # - The report is not fully present in attachments.
        if save_in_attachment and not res_ids:
            _logger.info('The PDF report has been generated from attachments.')
            return self._post_pdf(save_in_attachment), 'pdf'

        if self.get_wkhtmltopdf_state() == 'install':
            # wkhtmltopdf is not installed
            # the call should be catched before (cf /report/check_wkhtmltopdf) but
            # if get_pdf is called manually (email template), the check could be
            # bypassed
            raise UserError(_("Unable to find Wkhtmltopdf on this system. The PDF can not be created."))

        html = self.with_context(context).render_qweb_html(res_ids, data=data)[0]

        # Ensure the current document is utf-8 encoded.
        html = html.decode('utf-8')

        bodies, html_ids, header, footer, specific_paperformat_args = self.with_context(context)._prepare_html(html)

        pdf_content = self._run_wkhtmltopdf(
            bodies,
            header=header,
            footer=footer,
            landscape=context.get('landscape'),
            specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=context.get('set_viewport_size'),
        )
        if res_ids:
            _logger.info('The PDF report has been generated for records %s.' % (str(res_ids)))
            return self._post_pdf(save_in_attachment, pdf_content=pdf_content, res_ids=html_ids), 'pdf'
        return pdf_content, 'pdf'

    @api.model
    def render_qweb_html(self, docids, data=None):
        """This method generates and returns html version of a report.
        """
        # If the report is using a custom model to render its html, we must use it.
        # Otherwise, fallback on the generic html rendering.
        report_model_name = 'report.%s' % self.report_name
        report_model = self.env.get(report_model_name)

        if report_model is not None:
            data = report_model.get_report_values(docids, data=data)
        else:
            docs = self.env[self.model].browse(docids)
            data = {
                'doc_ids': docids,
                'doc_model': self.model,
                'docs': docs,
            }
        
        # custom code for set print-counter POS restaurant bill
        if self.report_name == 'kg_pos.kg_pos_restaurant_bill_report':
            if docids:
                orders = self.env[self.model].browse(docids)
                for order in orders:
                    if not order.print_from_button:
                        order.print_counter += 1
                    if order.print_from_button:
                        order.print_from_button = False
        # end of custom code

        # custom code -> no longer used
        if self.report_name == 'kg_pos.kg_pos_order_report':
            if not self.env.context.get('print_from_button', False):
                model = self.env[self.model].browse(docids)
                if 'REFUND' in model.lines.mapped('name')[0]:
                    payment_amount = sum(line.amount for line in model.statement_ids) - (model.amount_total)
                    change = payment_amount
                else:
                    payment_amount = model.statement_ids.filtered(lambda line:
                        (
                        line.amount > 0
                        )
                    ).mapped('amount')
                    total_payment_amount = sum(amount for amount in payment_amount)
                    total_order_amount = sum(line.price_subtotal_incl for line in model.lines)

                    if model.change != 0:
                        change = model.change
                    else:
                        change = total_payment_amount - total_order_amount
                
                pos_order_rec = model

                data = {
                    'doc_ids': docids,
                    'doc_model': self.model,
                    'docs': model,
                    'ids': pos_order_rec.ids,
                    'model': pos_order_rec,
                    'model_name': pos_order_rec._name,
                    'change': change,
                }

                model.print_counter += 1

                model.write({
                    'print_counter_name': '%s - duplicate %d' % (model.name, model.print_counter)
                })
        # end of custom code

        return self.render_template(self.report_name, data), 'html'