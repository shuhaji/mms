from odoo import api,fields,models,_


class KGNewPaymentListAP(models.TransientModel):
    _name = 'new.payment.list.ap'

    # date = fields.Date('Start Date', required=True)
    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    company_id = fields.Many2one(comodel_name='res.company',string='Company', required=True, default=lambda self:self.env.user.company_id.id)

    journal_id = fields.Many2one(
        'account.journal',
        'Payment Journal',
        required=True,
    )

    @api.multi
    def print_report(self):
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            # 'date': self.date,
            'company_id': self.company_id.id,
            'journal_id': self.journal_id.id,
        }
        return self.env.ref('kg_account.menu_report_new_payment_list_ap').report_action([], data=data)


