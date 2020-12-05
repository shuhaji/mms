from dateutil.parser import parse

from odoo import api, fields, models


class AccountMoveInitialBalanceRecalculation(models.TransientModel):
    _name = 'account.move.initial.balance.recalculation'

    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id.id)
    period = fields.Date('Period', required=True, default=fields.Date.today)

    @api.multi
    def calculate_initial_balance(self):
        query = """ select account_move_yearly_calculate_balance(%s, %s) """
        params = (self.company_id.id, parse(self.period).year - 1)
        self._cr.execute(query, params)
        query = """ select account_move_yearly_calculate_init_balance(%s, %s)"""
        params = (self.company_id.id, parse(self.period).year)
        self._cr.execute(query, params)
        return {
            'warning': {
                'title': 'Info',
                'message': 'Process Success',
            }
        }
