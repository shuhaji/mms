from odoo import api, fields, models, _


class WizardAPMutation(models.TransientModel):
    _inherit = 'wizard.kg.report.base'
    _name = 'wizard.kg.report.ap.mutation'
    _title = "KG Report - AP Mutation"

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)

    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id.id)
    account_id = fields.Many2one('account.account', string='Account')
    partner_id = fields.Many2many('res.partner', string='Partner')

    @api.onchange('account_id')
    def onchange_account_id(self):
        if not self.account_id:
            self.partner_id = None

    @api.multi
    def _get_data(self):
        get_ap_mutation = self.get_ap_mutation_data()
        self.report_has_logo = False  # sample report has logo

        data = {
            'config': {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'company_id': self.company_id.name,
                'partner_id': self.partner_id.ids,
                'account_id': self.account_id.id,
                'printed_by': self.env.user.name,
            },
            'data': get_ap_mutation
        }
        return data

    @api.multi
    def get_ap_mutation_data(self):
        where_account_clause, where_dest_account_clause, where_partner_clause = self.query_get_clause()

        partner_format_clause = tuple(self.partner_id.ids)
        if len(self.partner_id.ids) == 1:
            partner_format_clause = (self.partner_id.ids[0])

        query = """                   
                with z_kg_beginning_balance as (
                    select coalesce(s.partner_id, 0) as partner_id, s.account_id
                        , sum(case when a.internal_type = 'payable' then -1 else 1 end * (debit-credit)) as beginning_balance
                    from account_move_line s
                        left join account_move m on m.id = s.move_id
                        left join account_account a on a.id = s.account_id
                    where s.company_id = {company_id}                        
                        """ + where_account_clause + """
                        """ + where_partner_clause + """
                        and s."date" < '{start_date}'
                        and m.state = 'posted'
                        and a.internal_type = 'payable'
                    group by s.partner_id, s.account_id
                    having sum(debit-credit) != 0 
                )
                , z_invoice as (
                    select coalesce(s.partner_id, 0) as partner_id, s.account_id
                        , sum(case when s.amount_total_signed >= 0 then s.amount_total_signed else 0 end) invoice
                        , sum(case when s.amount_total_signed < 0 then s.amount_total_signed else 0 end) credit_invoice
                    from account_invoice s
                    where s.company_id = {company_id}                        
                        """ + where_account_clause + """
                        """ + where_partner_clause + """
                        and s.date_invoice between '{start_date}' and '{end_date}'
                        and s.state in ('open', 'paid')
                        and s.type = 'in_invoice'
                    group by s.partner_id, s.account_id
                ), 
                z_payment_adj as (
                    select coalesce(s.partner_id, 0) partner_id
                        , destination_account_id  as account_id                        
                        , sum(case when s.partner_type = 'supplier' and s.payment_type = 'outbound' then 1
                            when s.partner_type = 'supplier' and s.payment_type = 'inbound' then -1
                            else 0 end * s.amount) as payment
                        , sum(case when s.partner_type = 'supplier' and s.payment_type = 'outbound' then -1
                            when s.partner_type = 'supplier' and s.payment_type = 'inbound' then 1
                            else 0 end * coalesce(s.writeoff_amount, 0)) as adjustment
                    from account_payment s
                    where s.company_id = {company_id}
                        """ + where_dest_account_clause + """
                        """ + where_partner_clause + """
                        and s.payment_date between '{start_date}' and '{end_date}'
                        and s.partner_type = 'supplier'
                        and s.state in ('posted', 'sent', 'reconciled')
                    group by s.partner_id
                        , s.destination_account_id 
                ),
                z_withholding_tax as ( 
                    select coalesce(wtm.partner_id, 0) partner_id, s.account_id
                        , sum(wtm.amount) as wth_tax_amount                         
                    From withholding_tax_move wtm                          
                        left join account_move_line s on s.id = wtm.payment_line_id  
                        left join account_account a on a.id = s.account_id
                    where wtm.date between '{start_date}' and '{end_date}'
                        and wtm.state in ('due', 'paid')
                        and s.company_id = {company_id}
                        """ + where_account_clause + """
                        """ + where_partner_clause + """
                    group by wtm.partner_id, s.account_id
                )
                , z_partner as (
                    select distinct account_id, partner_id
                    from (select partner_id, account_id from z_kg_beginning_balance
                        union select partner_id, account_id from z_invoice
                        union select partner_id, account_id from z_payment_adj
                        union select partner_id, account_id from z_withholding_tax) s 
                    order by account_id, partner_id
                )
                select p.account_id, ac.name as account_name, p.partner_id , coalesce(rp.name, 'Unknown Partner') as partner_name
                    , coalesce(bl.beginning_balance,0) as beginning_balance, coalesce(i.invoice,0) as invoice, coalesce(i.credit_invoice,0) as credit_invoice
                    , coalesce(pa.payment,0) as payment, coalesce(pa.adjustment,0) as adjustment, coalesce(t.wth_tax_amount,0) as wth_tax_amount
                    , coalesce(bl.beginning_balance,0)+coalesce(i.invoice,0)-coalesce(i.credit_invoice,0)-coalesce(pa.payment,0)-coalesce(pa.adjustment,0)-coalesce(t.wth_tax_amount,0) as end_balance
                from 
                    z_partner p 
                    left join res_partner rp on rp.id = p.partner_id
                    left join account_account ac on ac.id = p.account_id
                    left join z_kg_beginning_balance bl on p.partner_id = bl.partner_id and p.account_id = bl.account_id
                    left join z_invoice i on p.partner_id = i.partner_id and p.account_id = i.account_id
                    left join z_payment_adj pa on p.partner_id = pa.partner_id and p.account_id = pa.account_id
                    left join z_withholding_tax t on p.partner_id = t.partner_id and p.account_id = t.account_id
                order by p.account_id , rp.name;                
                """
        final_query = query.format(
            company_id=self.company_id.id, start_date=self.start_date, end_date=self.end_date,
            account_id=self.account_id.id, partner_id=partner_format_clause)

        self.env.cr.execute(final_query)
        ap_mutation = self.env.cr.dictfetchall()

        return ap_mutation

    def query_get_clause(self):
        where_account_clause = ""
        if self.account_id:
            where_account_clause = "and s.account_id = {account_id}"

        where_dest_account_clause = ""
        if self.account_id:
            where_dest_account_clause = "and s.destination_account_id = {account_id}"

        where_partner_clause = ""
        if self.partner_id:
            where_partner_clause = "and s.partner_id in {partner_id}"
            if len(self.partner_id.ids) == 1:
                where_partner_clause = "and s.partner_id = {partner_id}"

        return where_account_clause, where_dest_account_clause, where_partner_clause

    @staticmethod
    def _define_report_name():
        return "/kg_account/static/rpt/APMutation.mrt"


#     @api.multi
#     def _get_data(self):
#         """ get data from database or any other source
#
#         :return: dict or list of dict
#         """
#         data = {
#             'start_date': self.start_date,
#             'end_date': self.end_date,
#             'company_id': self.company_id.id,
#             'partner_id': self.partner_id.ids,
#             'account_id': self.account_id.id,
#         }
#
#         res = self.get_report_values(data=data)
#
#         return {
#             "config": {
#                 "start_date": res['start_date'],
#                 "end_date": res['end_date'],
#                 "company_id": res['company_id'],
#                 "partner_id": self.partner_id.ids,
#                 "account_id": self.account_id.id,
#                 "printed_by": res['printed_by'],
#             },
#             "data_total": {
#                 "total_bg_balance": res['data_total'][0],
#                 "total_folio": res['data_total'][1],
#                 "total_creditnote": res['data_total'][2],
#                 "total_payment": res['data_total'][3],
#                 "total_adjustment": res['data_total'][4],
#                 "total_withholding_tax": res['data_total'][5],
#                 "total_all": res['data_total'][6],
#                 },
#             "data": res['docs']
#         }
#
#     def get_report_values(self, data=None):
#         res = self.env['report.kg_account.report_ap_mutation'].get_report_values(docids=None, data=data)
#
#         return res
#
#     def _define_report_name(self):
#         """ path to report file)
#         /app_name/path_to_file/report_name.mrt
#         example: "/kg_report_base/static/rpt/RegistrationCard.mrt"
#           kg_report_base is app name (module name)
#
#         :return: str
#         """
#
#         rpt = "/kg_account/static/rpt/APMutation.mrt"
#
#         return rpt

