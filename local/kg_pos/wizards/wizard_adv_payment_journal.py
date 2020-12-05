# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

class KGPOSWizardJournal(models.TransientModel):
    _name = 'wizard.select.journal'

    name = fields.Char(
        'Name'
    )

    company_id = fields.Many2one(
        'res.company',
        'Company',
        default=lambda self: self.env.user.company_id,
    )

    journal_id = fields.Many2one(
        'account.journal',
        'Journal',
        required=True,
    )

    @api.multi
    def button_confirm(self):
        for select in self:
            model_name = self.env.context.get('active_model', False)
            active_model = self.env[model_name].browse(self.env.context.get('active_id', False))
            session = active_model
            session.with_context(adv_payment_journal = select.journal_id).action_pos_session_close()

    @api.multi
    def button_cancel(self):
        for select in self:
            model_name = self.env.context.get('active_model', False)
            active_model = self.env[model_name].browse(self.env.context.get('active_id', False))
            res_id = active_model.id
            context = self.env.context
            active_model.write({
                'state': 'opened'
            })
            
            view = { 
                'name':_("POS Session"),
                'view_mode': 'form',
                'view_id': False,
                'view_type': 'form',
                'res_model': 'pos.session',
                'res_id': res_id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'self',
                'domain': '[]',
                'context': context
                }
            
            return view
