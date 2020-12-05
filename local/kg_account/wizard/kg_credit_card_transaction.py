from odoo import api, fields, models


class KGCreditCardTransaction(models.TransientModel):
    _name = 'kg.credit.card.transaction'

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)

    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id.id)

    journal_id = fields.Many2one(comodel_name='account.journal', string='Journal')

    @api.multi
    def calculate_cc_transaction(self):
        if self.journal_id:
            where_journal_id = "AND ab.journal_id = %s"
            params = (self.start_date, self.end_date, self.company_id.id, self.journal_id.id,
                      self.start_date, self.end_date, self.company_id.id, self.journal_id.id)
        else:
            where_journal_id = ""
            params = (self.start_date, self.end_date, self.company_id.id,
                      self.start_date, self.end_date, self.company_id.id)

        # insert or update, jika wizard di running ulang:
        #   utk company + tgl + kg_issuer_type yg sudah ada, harusnya terupdate (terkalkulasi ulang)!
        query = """
            with z_kg_acquirer_recalc as (
                SELECT n, company_id, journal_id, "date", issuer_type_id as kg_issuer_type_id, SUM(amount) AS amount,
                        1 as type, 0 as amount_applied, SUM(amount) AS amount_remain, SUM(amount) AS amount_transfer 
                FROM (
                    SELECT to_char(ab."date", 'YYYYMMDD') || '/' || 
                        trim(to_char(coalesce(abl.issuer_type_id, 999), '999')) as n, 
                    ab.company_id, ab.journal_id, ab."date", abl.issuer_type_id, 
                    SUM(abl.amount) AS amount, 1 AS type, 0 AS amount_applied, 
                    SUM(abl.amount) AS amount_remain, 
                    0 AS amount_transfer  
                    FROM public.account_bank_statement ab 
                    LEFT JOIN public.account_bank_statement_line abl ON ab.id = abl.statement_id 
                    LEFT JOIN public.account_journal aj ON ab.journal_id = aj.id 
                    WHERE ab."date" BETWEEN %s AND %s
                    AND aj.is_bank_edc_credit_card = TRUE 
                    AND ab.company_id = %s
                    """ + where_journal_id + """ 
                    GROUP BY ab.company_id, ab.journal_id, ab."date", abl.issuer_type_id
                    having SUM(abl.amount) != 0
                    UNION
                    SELECT to_char(payment_date, 'YYYYMMDD') || '/' || 
                        trim(to_char(coalesce(issuer_type_id, 999), '999')) as name, 
                    ab.company_id, journal_id, payment_date, issuer_type_id, 
                    SUM(amount) AS amount, 1 AS type, 0 AS amount_applied, SUM(amount) AS amount_remain, 
                    0 AS amount_transfer  
                    FROM public.account_payment ab 
                    LEFT JOIN public.account_journal aj ON ab.journal_id = aj.id 
                    WHERE payment_date BETWEEN %s AND %s
                    AND aj.is_bank_edc_credit_card = TRUE 
                    AND ab.is_advance_payment = TRUE 
                    AND ab.company_id = %s
                    """ + where_journal_id + """ 
                    GROUP BY ab.company_id, journal_id, payment_date, issuer_type_id
                    having sum(amount) != 0
                ) as Payment
                     GROUP BY n, company_id, journal_id, "date", issuer_type_id
            ),
            updated as (
                update kg_acquirer_transaction t
                set amount = s.amount
                    , amount_remain = s.amount - t.amount_applied
                    , amount_transfer = s.amount_transfer
                from z_kg_acquirer_recalc s
                where s.date = t.date and s.company_id = t.company_id and s.journal_id = t.journal_id 
                    and s.type = t.type
                    and coalesce(t.kg_issuer_type_id, -99) = coalesce( s.kg_issuer_type_id, -99)  
                returning t.date, t.company_id, t.journal_id, t.kg_issuer_type_id, t.type
            )
            insert into kg_acquirer_transaction 
            (name, company_id, journal_id, "date", kg_issuer_type_id, amount, type, amount_applied, 
                amount_remain, amount_transfer) 
            select * 
            from z_kg_acquirer_recalc s 
            where not exists (
                SELECT 1
                FROM updated t
                WHERE s.date = t.date and s.company_id = t.company_id and s.journal_id = t.journal_id 
                    and s.type = t.type
                    and coalesce(t.kg_issuer_type_id, -99) = coalesce( s.kg_issuer_type_id, -99)
            );        
        """
        self._cr.execute(query, params)
        return {
            'warning': {
                'title': 'Info',
                'message': 'Process Success',
            }
        }


