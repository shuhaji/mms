# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountPaymentReport(models.TransientModel):
    _inherit = "account.common.report"
    _name = 'account.payment.report'
    _description = 'Payment Report'

    company = fields.Many2one(comodel_name='res.company', string='Company', required=True,
                              default=lambda self: self.env.user.company_id.id)
    journal_id = fields.Many2one('account.journal', string='Payment Journal', required=True,
                                 domain=[('type', 'in', ('bank', 'cash'))])

    # @api.multi
    def _print_report(self, data):
        return self.env.ref('kg_account.action_report_payments').report_action(self, data=data)

    @api.multi
    def check_report(self):
        data = {}
        self.ensure_one()

        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'company', 'journal_id'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')

        return self.with_context(discard_logo_check=True)._print_report(data)
