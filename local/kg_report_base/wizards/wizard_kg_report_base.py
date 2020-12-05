import os

from dateutil import parser

from odoo import api,fields,models,_
from odoo.modules import get_module_path
from odoo.exceptions import UserError
from datetime import datetime
from io import StringIO
import json
import base64


class WizardExportPajakOnline(models.TransientModel):
    _name = 'wizard.kg.report.base'
    _title = "KG Report - Sample"
    working_date = fields.Date(default=fields.Date.context_today)

    report_data = fields.Char(default=None)
    report_has_logo = fields.Boolean(default=False)

    url_file_path = fields.Char(widget="url")
    file_path = fields.Char()
    file_name = fields.Char(default=False)
    show_file_binary = fields.Boolean(default=False)
    file_binary = fields.Binary()

    @api.multi
    def _get_data(self):
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
        self.report_has_logo = True  # sample report has logo
        return self._sample_data_reg_card()

    @api.multi
    def _get_data2(self):
        # jika butuh data dictionary yg ke dua utk report (jika tidak bisa dalam 1 json/dict)
        return False

    @api.multi
    def _get_data3(self):
        # jika butuh data dictionary yg ke tiga utk report (jika tidak bisa dalam 1 json/dict)
        return False

    @staticmethod
    def _define_report_name():
        """ path to report file)
        /app_name/path_to_file/report_name.mrt
        example: "/kg_report_base/static/rpt/RegistrationCard.mrt"
          kg_report_base is app name (module name)

        :return: str
        """
        return "/kg_report_base/static/rpt/RegistrationCard.mrt"
        # return "/kg_report_base/static/rpt/sample1.mrt"

    def _define_report_variables(self):
        """ define report variables

        key : report variable name
        value : variable value to be send to report
        is_image: if value is an image or not

        :return: list of KgReportVariable
        """
        variables = list()

        # contoh menambahkan variable:
        # variables.append(KgReportVariable(
        #     key="Address1",  # variable name in report
        #     value="ini alamat jl bla bla",
        # ).to_dict())
        return variables

    def _add_logo(self, variables):
        if self.report_has_logo:
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

    @api.multi
    def show_report(self):
        self.url_file_path = False
        # format all data (report name + data + variables)
        self._format_data_output()
        # refresh client form (reopen form and show report
        return self._reopen_form()

    def _format_data_output(self):
        # get data from database or any other source
        data = self._get_data()  # main report data
        data2 = self._get_data2()  # report data 2 (if needed)
        data3 = self._get_data3()  # report data 3
        # get report name
        report_name = "{name}?version={version}".format(
            name=self._define_report_name(),
            # version: jika report sudah diedit, agar di client otomatis refresh, ubah versionnya jg
            #   kadang di cache sama browser, utk mengatasi hal ini, ganti report version-nya
            version=datetime.now().timestamp()
        )
        variables = self._define_report_variables()
        variables = self._add_logo(variables)
        self.report_data = json.dumps({
            "reportName": report_name,
            "json": data,  # report data
            "json2": data2,  # report data 2
            "json3": data3,  # report data 3
            "variables": variables
        })

    @api.multi
    def _reopen_form(self):
        self.ensure_one()
        # return {"type": "ir.actions.do_nothing"}

        # jika view tampil sbg modal:
        target = 'new'
        # jika view sbg form biasa (bukan modal dialog)
        # target = 'inline'

        view_id = self.env['ir.ui.view'].search(
            [('model', '=', self._name), ('type', '=', 'form')])
        return {
            'context': self.env.context,
            'view_id': view_id.id,
            # 'name': "KG Report - Sample",
            "name": self._title,
            'type': 'ir.actions.act_window',
            'res_model': self._name,  # this model
            'res_id': self.id,  # the current wizard record
            'view_type': 'form',
            'view_mode': 'form',
            'target': target}

    @api.multi
    def save_data_to_json_file(self):
        # get data from database or any other source
        data = self._get_data()
        json_data = json.dumps(data)
        base_path = "/kg_report_base/static/outfile"

        self.file_name = "report_data.json"

        m_path = get_module_path('kg_report_base')
        folder_path = m_path + base_path.replace("/kg_report_base", "")
        os.makedirs(folder_path, exist_ok=True)

        self.file_path = folder_path + "/" + self.file_name + "?version=" + str(datetime.now().timestamp())
        self.url_file_path = base_path + "/" + self.file_name + "?version=" + str(datetime.now().timestamp())

        txt_file = open(folder_path + "/" + self.file_name, 'w')
        txt_file.write(json_data)
        txt_file.close()
        return self._reopen_form()

    @api.multi
    def save_json_data_to_binary_field(self):
        data = self._get_data()
        string_out = self.write_data_to_stream(data)
        self.show_file_binary = True
        self.file_name = "data.json"
        self.file_binary = base64.b64encode(bytes(string_out, "utf-8"))
        return self._reopen_form()

    def write_data_to_stream(self, data):
        # override this method to write data to text file format

        # in this example, data is in json format, so we convert to string first
        data = json.dumps(data)
        return data
        # example format json data to text
        # example: convert data to text file in stream via StringIO
        # stream_out = StringIO()
        # for row in data:
        #     stream_out.write("{name}--abc".format(name=row.get('field_name1')))
        #     stream_out.write("\n")  # new line
        # return stream_out.getvalue()

    def _sample_data_reg_card(self):
        return {
            "IsWeekendRate": False,
            "IsNoCancellation": False,
            "IsNoChangeReservation": False,
            "Address1": "Jl. Kembang Wangi III Blok K-7/II 010/002",
            "Address2": "kembangan selatan",
            "CityDescription": "Jakarta",
            "NationalityDescription": "",
            "EmailAddress": "",
            "IdentityNo": "3173086903650002",
            "JobTitle": "Mengurus Rumah Tangga",
            "CompanyAddress1": "615 Lorong 4 Toa Payoh #01-01",
            "CompanyAddress2": " ",
            "TitleDescription": "Mr.",
            "PaymentTypeDescription": "CASH",
            "CompanyType": 4,
            "ReservationDate": "2018-12-03T00:00:00",
            "ReservationBy": "Evelina",
            "PhoneNo": "08118205233",
            "ReservationStatus": "T",
            "LastReservationStatus": "T",
            "ArrivalDate": "2018-12-01T00:00:00",
            "DepartureDate": "2018-12-02T00:00:00",
            "ExpectedDepartureDate": "2018-12-02T00:00:00",
            "ArrivalTime": "14:00:00",
            "DepartureTime": "12:00:00",
            "Nights": 1,
            "CompanyId": 11604,
            "GuestId": 70,
            "ActualType": "SMRT DBL  ",
            "TypeId": "SMRT DBL  ",
            "RoomNo": " ",
            "Person": 2,
            "Pax": 2,
            "Adult": 2,
            "Child": 0,
            "RateType": "BAR",
            "RateId": "BAR1801",
            "Currency": "IDR",
            "TaxCode": "I",
            "OriginalRate": 620000,
            "PromoId": 0,
            "PromoType": 0,
            "PromoDiscountType": 0,
            "PromoDiscountPct": 0,
            "RoomRate": 620000,
            "DiscountId": 0,
            "DiscountType": 0,
            "DiscountRate": 0,
            "ExtraBed": 0,
            "ExtraBedCharge": 0,
            "AdditionalRoomCharge": 0,
            "AdditionalStartDate": "1900-01-01T00:00:00",
            "AdditionalEndDate": "1900-01-01T00:00:00",
            "RoomToCharge": "",
            "FolioToCharge": 0,
            "MarketId": 8,
            "SourceId": 7,
            "SalesId": 0,
            "AccountExecutiveId1": 0,
            "AccountExecutiveId2": 0,
            "CarrierIdArrival": 0,
            "CarrierIdDeparture": 0,
            "GroupId": 0,
            "GroupPairId": 0,
            "KeyCardCount": 0,
            "SharedType": 0,
            "ChannelManagerId": "0",
            "ChannelManagerAttribute": "",
            "IsEarningPoint": False,
            "IsMoveRoom": False,
            "IsGroupInHouse": False,
            "IsGroupMaster": False,
            "IsPromotion": False,
            "IsAllotment": False,
            "IsUpgrade": False,
            "IsGuarantee": False,
            "IsBlockingRoom": False,
            "IsSharedCharge": False,
            "IsNoPOSTransaction": True,
            "IsSendToIPTV": False,
            "IsPickupCharged": False,
            "IsIncognito": False,
            "IsDontDisturb": False,
            "IsChangeRate": False,
            "IsDeposit": False,
            "SpecialRequest": "0",
            "PaymentType": "C",
            "PaymentRemark": "",
            "CardId": 1,
            "CardNumber": "0",
            "CardName": "",
            "CreditLimit": 0,
            "CancelId": 0,
            "ExtendDate": "1900-01-01T00:00:00",
            "CheckInBy": "",
            "Attribute": "",
            "Note": " ",
            "GuestStatusId": 1,
            "IsNewGroup": False,
            "GroupDescription": "",
            "AddFolioId": 0,
            "AddRoomCharge": 0,
            "AddStartDate": "1900-01-01T00:00:00",
            "AddEndDate": "1900-01-01T00:00:00",
            "AddRemark": "",
            "Message1": "",
            "MessageStartDate1": "2018-12-01T00:00:00",
            "MessageEndDate1": "2018-12-02T12:00:00",
            "Message2": "",
            "MessageStartDate2": "1900-01-01T00:00:00",
            "MessageEndDate2": "1900-01-01T00:00:00",
            "WakeUpCall": 0,
            "WakeUpCallTime": "1900-01-01T00:00:00",
            "ReservationId": 78,
            "SystemDate": "0001-01-01T00:00:00",
            "GuestName": "Evelina",
            "GuestName2": "",
            "CompanyName": "Asia Travel.com",
            "MembershipNo": "",
            "RowChange": "NEW_ROW",
            "CreatedDate": "2018-12-03T15:42:36.493",
            "UpdatedDate": "2018-12-03T15:42:36.493",
            "CreatedBy": "admin1000",
            "UpdatedBy": "admin1000",
            "UserId": "",
            "Remark": "asdfvb",
            "IsNotUsed": False,
            "Mode": "",
            "ReturnMessage": "",
            "ROW_ID": 0,
            "HotelId": 1000,
            "HotelName": ""
        }


class KgReportVariable(object):

    def __init__(self, key, value, is_image=False, format_value="url"):
        self.key = key
        self.value = value
        self.is_image = is_image
        self.format_value = format_value  # this is format value for image (str or url path)

    def to_dict(self):
        return {
            "key": self.key,
            "value": self.value,
            "is_image": self.is_image,
            "format_value": self.format_value
        }
