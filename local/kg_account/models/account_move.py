# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError


class KGAccountMove(models.Model):
    _inherit = 'account.move'

    show_post = fields.Boolean(
        'Show Post',
        default=True,
    )

    # untuk transaksi transfer, related journal id akan berisi journal id pasangannya,
    # misal dari journal A transfer ke Journal B:
    #   di account Move A, field ini terisi B
    #   di account move B, field ini terisi A
    related_journal_id = fields.Many2one(
        'account.journal', string='Journal', required=False,
        states={'posted': [('readonly', True)]})

    @api.multi
    @api.onchange('date')
    def onchange_date(self):
        for move in self:
            current_user = self.env['res.users'].browse(self.env.context.get('uid', False))
            current_date = fields.Date.today()
            date_selected = move.date
            if date_selected >= current_date:
                move.show_post = True
            elif date_selected < current_date:
                if not current_user.has_group('kg_account.group_allow_create_back_date_journal_entry'):
                    move.show_post = False
                else:
                    move.show_post = True

    @api.multi
    @api.constrains('date')
    def check_date(self):
        for move in self:
            current_user = self.env['res.users'].browse(self.env.context.get('uid', False))
            current_date = fields.Date.today()
            date_selected = move.date
            if date_selected < current_date:
                if not current_user.has_group('kg_account.group_allow_create_back_date_journal_entry'):
                    raise UserError(_('You do not have access rights to create a back date journal entry!'))

    @api.multi
    def assert_balanced(self):
        if not self.ids:
            return True
        prec = self.env['decimal.precision'].precision_get('Account')

        self._cr.execute("""
            SELECT      move_id, sum(debit) debit, sum(credit) as credit, abs(sum(debit) - sum(credit)) as balance
            FROM        account_move_line
            WHERE       move_id in %s
            GROUP BY    move_id
            HAVING      abs(sum(debit) - sum(credit)) > %s
            """, (tuple(self.ids), 10 ** (-max(5, prec))))
        unbalance_moves = self._cr.dictfetchall()
        if len(unbalance_moves) != 0:
            # unbalance_move_ids = [move.get('move_id') for move in unbalance_moves]
            # move_lines = []
            # for line in self.line_ids:
            #     if line.move_id.id in unbalance_move_ids:
            #         move_lines.append('{ref},{credit},{debit},{account_id},{account_name},{name}'.format(
            #             ref=line.move_id.ref,
            #             credit=line.credit,
            #             debit=line.debit,
            #             account_id=line.account_id.id,
            #             account_name=line.account_id.name,
            #             name=line.name
            #         ))
            raise UserError(_("Cannot create unbalanced journal entry."))
            # raise UserError(_("Cannot create unbalanced journal entry.\n"
            #                   "All Move Lines (ref,credit,debit,account,names):\n" + ';\n'.join(move_lines)))
        return True

    @api.multi
    def _check_lock_date(self):
        for move in self:
            move.env['account.period'].check_lock_period_account_move(self, move)
        super(KGAccountMove, self)._check_lock_date()

