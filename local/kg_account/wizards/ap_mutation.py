from odoo import api, fields, models,_


class KGAPMutationWizard(models.TransientModel):
    _name = 'ap.mutation.wizard'

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, default=lambda self:self.env.user.company_id.id)

    # journal_id = fields.Many2one(
    #     'account.journal',
    #     'Invoice Journal',
    #     required=True,
    #     domain="[('type', '=', 'purchase'), ('company_id', '=', company_id)]",
    # )

    @api.multi
    def print_report(self):
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'company_id': self.company_id.id,
            # 'journal_id': self.journal_id.id,
        }

        return self.env.ref('kg_account.menu_report_ap_mutation').report_action([], data=data)


