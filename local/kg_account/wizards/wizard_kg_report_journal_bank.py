import os

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.modules import get_module_path
from datetime import datetime
import json


class WizardJournalAuditBank(models.TransientModel):
    _inherit = ['wizard.kg.report.base', 'account.print.journal']
    _name = 'wizard.kg.report.journal.bank'
    _title = "KG Report - Journal Audit Bank"

    report_type = fields.Selection([('receipt', 'Bank Receipt'), ('payment', 'Bank Payment'), ], 'Report Type',
                                   required=True, default='receipt')
    journal_ids = fields.Many2many('account.journal', string='Journals', required=True, default=None)
    payment_type = fields.Selection([('inbound', 'Receivable'), ('outbound', 'Payable'),
                                     ('transfer', 'Transfer'), ('journal', 'Journal Entry'),], 'Payment Type')

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
        data = self.get_param()

        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        res = self.get_report_values(data)

        res2 = self.get_report_values2(data)

        return {
            "data1": res,
            "data2": res2
        }

    def get_report_values(self, data=None):

        cr = self.env.cr

        current_company, end_date, sql_sort, start_date, \
            where_journal_id, where_state, where_journal_id_sum, where_payment_type = self.query_get_clause(data)

        query = """
            select am.name as move_name, aml.date, aa.code, aa.name as acc_name
                ,rp."name" as partner_name	
                ,aml."name" as lname
                ,aml.debit, aml.credit	
                ,aj."name" as jname                
                ,aj.id as journal_id
                ,aml.id
                ,case when aml.debit > aml.credit then 'D' 
                 when aml.debit < aml.credit then 'K' 
                 else '' end as tipe
                ,case when aml.debit >= aml.credit then 'XXX'                 
                 else 'X' || trim(to_char(aml.id, '999999')) end as sum_debit
                ,case when aml.credit >= aml.debit then 'XXX'                 
                 else 'X' || trim(to_char(aml.id, '999999')) end as sum_credit 
                ,aml.ref
                ,case when coalesce(ap.payment_type,'') = 'transfer' then 'Transfers'
                 when coalesce(ap.payment_type,'') = 'inbound' then 'Receivable'
                 when coalesce(ap.payment_type,'') = 'outbound' then 'Payable'
                 else 'Journal Entry' end as journal_payment_type               
            from account_move am
            left join account_move_line aml on am.id = aml.move_id
            left join account_payment ap on aml.payment_id = ap.id
            left join res_partner rp on rp.id = aml.partner_id
            left join account_account aa on aa.id = aml.account_id
            left join account_journal aj on aml.journal_id = aj.id                
            where 1 = 1
            and aml."date" between %s AND %s
            and am.company_id = %s
            """ + where_state + """   
            """ + where_payment_type + """
            """ + where_journal_id + """ 
            ORDER BY journal_payment_type, """ + sql_sort + """  
        """
        params = (start_date, end_date, current_company.id)
        self._cr.execute(query, params)
        res = cr.dictfetchall()

        # return self.env['report.account.report_journal'].get_report_values(docids=None, data=data)
        return res

    def query_get_clause(self, data):
        current_user = self.env['res.users'].browse(self.env.context.get('uid', False))
        current_company = current_user.company_id
        where_state = "AND am.state = 'posted' "
        sql_sort = "aml.date, am.id, aa.code"
        where_journal_id = ""
        where_journal_id_sum = ""
        journal_ids = data['form']['journal_ids']
        start_date = data['form']['date_from']
        end_date = data['form']['date_to']

        payment_type = data['form']['payment_type']
        if not payment_type:
            where_payment_type = ""
        elif payment_type == 'journal':
            where_payment_type = "AND coalesce(ap.payment_type,'') = ''"
        else:
            where_payment_type = "AND coalesce(ap.payment_type,'') = '" + payment_type + "'"

        if data['form']['target_move'] == 'all':
            where_state = ""
        if data['form']['target_move'] == 'move_name':
            sql_sort = "am.name, am.id, aa.code"
        if journal_ids:
            ids = [journal.id for journal in
                   self.env['account.journal'].search([('id', 'in', journal_ids)])]
            ids = list(map(str, ids))

            where_journal_id = "AND aj.id IN ( " + ', '.join(ids) + " ) "
            where_journal_id_sum = "AND aml.journal_id IN ( " + ', '.join(ids) + " ) "
        return current_company, end_date, sql_sort, start_date, \
            where_journal_id, where_state, where_journal_id_sum, where_payment_type

    def get_param(self):
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids',
                                  'target_move', 'sort_selection', 'report_type', 'payment_type'])[0]
        # used_context = self._build_contexts(data)
        # data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')

        return data

    @api.multi
    def get_report_values2(self, data=None):

        cr = self.env.cr

        current_company, end_date, sql_sort, start_date, \
            where_journal_id, where_state, where_journal_id_sum, payment_type = self.query_get_clause(data)

        query = """
            with z_base_amount as (
            select rel.account_tax_id, ax."name" as tax_name, SUM(aml.balance) as base_amount
            from account_move_line_account_tax_rel rel
            left join account_tax ax on ax.id = rel.account_tax_id
            left join account_move_line aml on aml.id = rel.account_move_line_id 
            left join account_move am on am.id = aml.move_id            
            where aml."date" between %s AND %s
            and am.company_id = %s
            """ + where_state + """  
            """ + where_journal_id_sum + """            
            group by rel.account_tax_id, ax."name"
            )
            select z.account_tax_id, z.tax_name, z.base_amount
                ,case when aj."type" = 'sale' then SUM(aml.debit-aml.credit) * -1 
                 else SUM(aml.debit-aml.credit) 
                 end as tax_amount	
                ,aml.journal_id 
            from account_move am
            left join account_move_line aml on am.id = aml.move_id
            join z_base_amount z on z.account_tax_id = aml.tax_line_id
            left join account_journal aj on aml.journal_id = aj.id
            where aml."date" between %s AND %s
            and am.company_id = %s
            """ + where_state + """  
            """ + where_journal_id_sum + """             
            group by z.account_tax_id, z.tax_name, z.base_amount, aml.journal_id, aj."type"  
        """
        params = (start_date, end_date, current_company.id, start_date, end_date, current_company.id)
        self._cr.execute(query, params)
        res = cr.dictfetchall()

        # return self.env['report.account.report_journal'].get_report_values(docids=None, data=data)
        return res

    @api.multi
    def _get_data2(self):
        # jika butuh data dictionary yg ke tiga utk report (jika tidak bisa dalam 1 json/dict)
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
        return "/kg_account/static/rpt/JournalAuditBank.mrt"

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

        data = self.get_param()
        current_user = self.env['res.users'].browse(self.env.context.get('uid', False))
        current_company = current_user.company_id

        variables.append(KgReportVariable(
            key="Company",  # variable name in report
            value=current_company.name,
        ).to_dict())

        variables.append(KgReportVariable(
            key="Sort",  # variable name in report
            value=dict(self._fields['sort_selection'].selection).get(data['form']['sort_selection']),
        ).to_dict())

        variables.append(KgReportVariable(
            key="Target",  # variable name in report
            value=dict(self._fields['target_move'].selection).get(data['form']['target_move']),
        ).to_dict())

        variables.append(KgReportVariable(
            key="Tipe",  # variable name in report
            # value=dict(self._fields['report_type'].selection).get(data['form']['report_type']),
            value=data['form']['report_type'],
        ).to_dict())

        variables.append(KgReportVariable(
            key="GM",  # variable name in report
            value=current_company.general_manager if current_company.general_manager else "",
        ).to_dict())

        variables.append(KgReportVariable(
            key="AM",  # variable name in report
            value=current_company.accounting_manager if current_company.accounting_manager else "",
        ).to_dict())

        variables.append(KgReportVariable(
            key="GC",  # variable name in report
            value=current_company.general_cashier if current_company.general_cashier else "",
        ).to_dict())

        variables.append(KgReportVariable(
            key="UserPrint",  # variable name in report
            value=self.env.user.name if self.env.user.name else "",
        ).to_dict())

        return variables
    #
    # def _add_logo(self, variables):
    #     if self.report_has_logo:
    #         # logo = self.env.user.company_id.logo
    #         # str_logo = logo.decode('utf-8')
    #         logo_url_path = "{path}?company={company_id}&version={version}".format(
    #             path="/web/binary/company_logo",
    #             company_id=self.env.user.company_id.id,
    #             # version: jika report sudah diedit, agar di client otomatis refresh, ubah versionnya jg
    #             #   kadang di cache sama browser, utk mengatasi hal ini, ganti url image version-nya
    #             version=datetime.now().timestamp()
    #         )
    #         variables.append(KgReportVariable(
    #             key="LogoImage",
    #             value=logo_url_path,
    #             is_image=True,
    #             format_value='url'  # url or str (string from binary)
    #         ).to_dict())
    #     return variables

    # @api.multi
    # def show_report(self):
    #     self.url_file_path = False
    #     # format all data (report name + data + variables)
    #     self._format_data_output()
    #     # refresh client form (reopen form and show report
    #     return self._reopen_form()

    # def _format_data_output(self):
    #     # get data from database or any other source
    #     data = self._get_data()
    #     # get report name
    #     report_name = "{name}?version={version}".format(
    #         name=self._define_report_name(),
    #         # version: jika report sudah diedit, agar di client otomatis refresh, ubah versionnya jg
    #         #   kadang di cache sama browser, utk mengatasi hal ini, ganti report version-nya
    #         version=datetime.now().timestamp()
    #     )
    #     variables = self._define_report_variables()
    #     variables = self._add_logo(variables)
    #     self.report_data = json.dumps({
    #         "reportName": report_name,
    #         "json": data,  # report data
    #         "json2": self._get_data2(),  # report data 2
    #         "json3": self._get_data3(),  # report data 3
    #         "variables": variables
    #     })

    # @api.multi
    # def _reopen_form(self):
    #     # return {"type": "ir.actions.do_nothing"}
    #
    #     # jika view tampil sbg modal:
    #     target = 'new'
    #     # jika view sbg form biasa (bukan modal dialog)
    #     # target = 'inline'
    #
    #     return {
    #         'context': self.env.context,
    #         # 'view_id': view_id,
    #         "name": "Journal Audit",
    #         'type': 'ir.actions.act_window',
    #         'res_model': self._name,  # this model
    #         'res_id': self.id,  # the current wizard record
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'target': target}

    # @api.multi
    # def save_data_to_json_file(self):
    #     # get data from database or any other source
    #     data = self._get_data()
    #     json_data = json.dumps(data)
    #     base_path = "/kg_account/static/outfile"
    #
    #     self.file_name = "report_data.json"
    #
    #     m_path = get_module_path('kg_account')
    #     folder_path = m_path + base_path.replace("/kg_account", "")
    #     os.makedirs(folder_path, exist_ok=True)
    #
    #     self.file_path = folder_path + "/" + self.file_name + "?version=" + str(datetime.now().timestamp())
    #     self.url_file_path = base_path + "/" + self.file_name + "?version=" + str(datetime.now().timestamp())
    #
    #     txt_file = open(folder_path + "/" + self.file_name, 'w')
    #     txt_file.write(json_data)
    #     txt_file.close()
    #     return self._reopen_form()

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
