import os

from dateutil import parser

from odoo import api,fields,models,_
from odoo.modules import get_module_path
from odoo.exceptions import UserError
from odoo.addons.kg_pos.controllers.kg_tax_online_export import KgApiTaxOnlineExport

from datetime import datetime
import time
from io import BytesIO
import xlsxwriter
import base64


class WizardExportPajakOnline(models.TransientModel):
    _name = 'wizard.export.pajak.online'

    working_date = fields.Date(default=fields.Date.context_today)
    get_data_from_pms = fields.Boolean(default=True, string="Get Data From PMS")
    url_file_path = fields.Char(widget="url")
    file_path = fields.Char()
    file_name = fields.Char(default='')
    data = fields.Binary('File', readonly=True)
    name = fields.Char('Filename', readonly=True)
    state_position = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    is_excel = fields.Boolean()

    @api.multi
    def generate_txt(self):
        self.generate_file(is_excel=False)
        return self._reopen_form()

    @api.multi
    def generate_excel(self):
        self.generate_file(is_excel=True)
        return self._reopen_form()

    @api.multi
    def generate_file(self, is_excel=False):
        company = self.env.user.company_id
        nopd_code = company.nopd_code.replace(".", "")
        # nopd_code = "1061704050001"
        if is_excel:
            file = None
            worksheet1, workbook, fp = self._prepare_file_excel(nopd_code, self.working_date)
        else:
            file = self._prepare_file_text(nopd_code, self.working_date)
            worksheet1 = workbook = fp = None

        # retrieve transaction data from PMS (API PMS)
        if self.get_data_from_pms:
            pms_data = self.env['pos.helpers'].get_pms_tax_online(working_date=self.working_date)
        else:
            pms_data = []
        if pms_data:
            row_no_start_from = len(pms_data)
        else:
            row_no_start_from = 0
        # retrieve data transaksi POS from database
        data = KgApiTaxOnlineExport.get_data(
            env=self.env,
            company_id=company.id,
            pos_date=self.working_date
        )
        # process data to file
        if company.region_name == 'surabaya' or is_excel:
            # surabaya --> Excel
            # write PMS data first
            self.write_pms_data_to_file(data=pms_data, worksheet=worksheet1, txt_file=None, format_output='sby')
            # write Odoo POS data
            result = KgApiTaxOnlineExport.generate_for_jakarta(
                data, format_output='sby', show_tax_amount=True,
                txt_file=None,
                worksheet=worksheet1, row_no_start_from=row_no_start_from
            )
        elif company.region_name == 'bali':
            # write PMS data first
            self.write_pms_data_to_file(data=pms_data, worksheet=None, txt_file=file, format_output='txt')
            # write Odoo POS data
            result = KgApiTaxOnlineExport.generate_for_bali(data, txt_file=file)
        elif company.region_name == 'jakarta':
            # write PMS data first
            self.write_pms_data_to_file(data=pms_data, worksheet=None, txt_file=file, format_output='txt')
            # write Odoo POS data
            result = KgApiTaxOnlineExport.generate_for_jakarta(
                data, format_output='txt', show_tax_amount=False, txt_file=file, row_no_start_from=row_no_start_from)
        else:
            raise UserError("Region user belum didefinisikan di master Company user ini!")

        self._save_file(file, is_excel, workbook, fp, result)

    @staticmethod
    def write_pms_data_to_file(data, worksheet=None, txt_file=None, format_output=None):
        row_no = 0
        for row_data in data:
            if format_output != 'txt' or worksheet:
                # format not text --> expect dictionary, or output to excel

                row_data = KgApiTaxOnlineExport.jakarta_dict(
                    True,
                    row_data.get('ReferenceId1'), row_data.get('ReferenceId2'), row_data.get('TaxCode'),
                    row_data.get('TrxDateLong'), row_data.get('Description'), row_data.get('Amount'),
                    row_data.get('Flag'),
                    int_to_str(row_data.get('TaxAmount')))
            if txt_file:
                data_string = row_data.get('DataString')
                txt_file.write(data_string + "\n")
            elif worksheet:
                KgApiTaxOnlineExport.write_excel(row_no, row_data, worksheet)
            row_no += 1
        return len(data)

    @api.multi
    def _prepare_file(self, nopd_code, working_date, extension=".txt"):
        export_date_name = parser.parse(working_date)
        export_date_name = datetime.strftime(export_date_name, "%Y%m%d000000")

        self.file_name = "T" + nopd_code + "_" + export_date_name + extension
        base_path = "/kg_pos/static/export_pajak_online"

        m_path = get_module_path('kg_pos')
        folder_path = m_path + base_path.replace("/kg_pos", "")
        os.makedirs(folder_path, exist_ok=True)

        self.file_path = folder_path + "/" + self.file_name
        self.url_file_path = base_path + "/" + self.file_name + "?version=" + str(datetime.now().timestamp())
        return folder_path

    @api.multi
    def _prepare_file_text(self, nopd_code, working_date):
        folder_path = self._prepare_file(nopd_code, working_date, ".txt")
        txt_file = open(folder_path + "/" + self.file_name, 'w')
        return txt_file

    @api.multi
    def _prepare_file_excel(self, nopd_code, working_date):
        self._prepare_file(nopd_code, working_date, ".xlsx")

        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        workbook.add_format()
        worksheet1 = workbook.add_worksheet("Report Excel")

        return worksheet1, workbook, fp

    @api.multi
    def _save_file(self, txt_file, is_excel, workbook=None, fp=None, result=None):
        if not is_excel:
            txt_file.close()
            file_encoded = None
            # save to binary field (utk link download di form)
            # file_obj = open(self.file_path, "r")
            # file_string = file_obj.read()
            if result:
                file_string = '\n'.join(result)
                file_encoded = base64.encodebytes(file_string.encode())
            # file_obj.close()
        else:
            workbook.close()
            file_encoded = base64.encodebytes(fp.getvalue())
            fp.close()
        self.write({'is_excel': is_excel, 'data': file_encoded, 'state_position': 'get'})

    @api.multi
    def _reopen_form(self):
        return {"type": "ir.actions.do_nothing"}

        # return {
        #     'context': self.env.context,
        #     # 'view_id': view_id,
        #     'type': 'ir.actions.act_window',
        #     'res_model': self._name,  # this model
        #     'res_id': self.id,  # the current wizard record
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'target': 'new'}


def int_to_str(var):
    return str(var).replace(".0", "")
