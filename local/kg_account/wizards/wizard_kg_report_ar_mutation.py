from odoo import api, fields, models, _


class WizardARMutation(models.TransientModel):
    _inherit = 'wizard.kg.report.base'
    _name = 'wizard.kg.report.ar.mutation'
    _title = "KG Report - AR Mutation"

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)

    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id.id)

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
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'company_id': self.company_id.id,
        }

        res = self.get_report_values(data=data)

        return {
            "config": {
                "start_date": res['start_date'],
                "end_date": res['end_date'],
                "company_id": res['company_id'],
                "printed_by": res['printed_by'],
            },
            "data_total": {
                "total_bg_balance": res['data_total'][0],
                "total_folio": res['data_total'][1],
                "total_creditnote": res['data_total'][2],
                "total_payment": res['data_total'][3],
                "total_adjustment": res['data_total'][4],
                "total_all": res['data_total'][5],
                },
            "data": res['docs']
        }

    def get_report_values(self, data=None):
        res = self.env['report.kg_account.report_ar_mutation_pdf'].get_report_values(docids=None, data=data)

        return res

    def _define_report_name(self):
        """ path to report file)
        /app_name/path_to_file/report_name.mrt
        example: "/kg_report_base/static/rpt/RegistrationCard.mrt"
          kg_report_base is app name (module name)

        :return: str
        """

        rpt = "/kg_account/static/rpt/ARMutation.mrt"

        return rpt

        # return "/kg_report_base/static/rpt/sample1.mrt"
