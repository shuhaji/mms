# Copyright 2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import json
import time
from datetime import datetime
from io import BytesIO

from odoo import models, fields, api
from odoo.addons.kg_report_base.wizards.wizard_kg_report_base import KgReportVariable
import logging

from odoo.http import request

_logger = logging.getLogger(__name__)


class KgReportActionBase(models.TransientModel):
    """ View Report without KG Report Wizard
    direct view KG Report - view menu Action Print (.mrt)

    """
    _name = 'report.kg_report_action_abstract'

    # change this report title accordingly
    _title = "KG Report"

    @api.model
    def _get_records_for_report(self, doc_ids, data, active_model):
        """
        Returns objects for xlx report.  From WebUI these
        are either as doc_ids taken from context.active_ids or
        in the case of wizard are in data.  Manual calls may rely
        on regular context, setting doc_ids, or setting data.

        :param doc_ids: list of integers, typically provided by
            qwebactionmanager for regular Models.
        :param data: dictionary of data, if present typically provided
            by qwebactionmanager for TransientModels.
        :param ids: list of integers, provided by overrides.
        :return: recordset of active model for ids.
        """
        if doc_ids:
            ids = doc_ids
        elif data and 'context' in data:
            ids = data["context"].get('active_ids', [])
        else:
            ids = self.env.context.get('active_ids', [])
        return self.env[active_model].browse(ids)

    @api.model
    def get_report_data(self, doc_ids, data, active_model, **kwargs):
        object_ids = doc_ids.split(",") if ("," in doc_ids) else doc_ids
        if isinstance(object_ids, list):
            object_ids = [int(obj_id) for obj_id in object_ids]
        else:
            object_ids = int(object_ids)
        records = self._get_records_for_report(object_ids, data, active_model)
        # format data into json and put it to field: self.report_data
        report_data = self._format_data_output(object_ids, data, records)
        return report_data

    @api.model
    def _format_data_output(self, doc_ids, data, records):
        # get data from database or any other source
        data = self._get_data(doc_ids, data, records)  # main report data
        data2 = self._get_data2(doc_ids, data, records)  # report data 2 (if needed)
        data3 = self._get_data3(doc_ids, data, records)  # report data 3
        # get report name
        report_name = "{name}?version={version}".format(
            name=self._define_report_name(doc_ids, data, records),
            # version: jika report sudah diedit, agar di client otomatis refresh, ubah versionnya jg
            #   kadang di cache sama browser, utk mengatasi hal ini, ganti report version-nya
            version=datetime.now().timestamp()
        )
        variables = self._define_report_variables(True)
        report_data = json.dumps({
            "reportName": report_name,
            "json": data,  # report data
            "json2": data2,  # report data 2
            "json3": data3,  # report data 3
            "variables": variables
        })
        return report_data

    @api.model
    def _define_report_name(self, doc_ids, data, records):
        # define mrt report name here
        raise NotImplementedError()

    @api.model
    def _get_data(self, doc_ids, data, records, **kwargs):
        """ get data from database or any other source

        :return: dict or list of dict
        """
        # return {
        #     "test": "abc", "test2": 123
        # }
        # return [
        #     {"test": "abc", "test2": 123},
        #     {"test": "cde", "test2": 124}
        # ]
        # multi key data:
        # return {
        #     "companyInfo": {"name": "abc", "address": "alamat mana saja"},
        #     "reportData": [
        #         {"test": "abc", "test2": 123},
        #         {"test": "cde", "test2": 124}
        #     ]
        # }
        # self.report_has_logo = True  # sample report has logo
        raise NotImplementedError()

    @api.model
    def _get_data2(self, doc_ids, data, records, **kwargs):
        # jika butuh data dictionary yg ke dua utk report (jika tidak bisa dalam 1 json/dict)
        # inherit this class and
        #   format data to dict/json object for report
        return False

    @api.model
    def _get_data3(self, doc_ids, data, records, **kwargs):
        # jika butuh data dictionary yg ke dua utk report (jika tidak bisa dalam 1 json/dict)
        # inherit this class and
        #   format data to dict/json object for report
        return False

    @api.model
    def _define_report_variables(self, report_has_logo=True):
        """ define report variables

        key : report variable name
        value : variable value to be send to report
        is_image: if value is an image or not

        :return: list of KgReportVariable
        """
        variables = list()
        variables = self._add_logo(variables, report_has_logo)
        # contoh menambahkan variable:
        # variables.append(KgReportVariable(
        #     key="Address1",  # variable name in report
        #     value="ini alamat jl bla bla",
        # ).to_dict())
        return variables

    @api.model
    def _add_logo(self, variables, report_has_logo=True):
        if report_has_logo:
            # logo = self.env.user.company_id.logo
            # str_logo = logo.decode('utf-8')
            logo_url_path = "{path}?company={company_id}&version={version}".format(
                path="/web/binary/company_logo",
                company_id=self.env.user.company_id.id,
                # version: jika report sudah diedit, agar di client otomatis refresh, ubah versionnya jg
                #   kadang di cache sama browser, utk mengatasi hal ini, ganti url image version-nya
                version=datetime.now().timestamp()
            )
            variables.append(KgReportVariable(
                key="LogoImage",
                value=logo_url_path,
                is_image=True,
                format_value='url'  # url or str (string from binary)
            ).to_dict())
        return variables
