from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class KgCrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    name = fields.Char(compute='_compute_line_name')
    account_id = fields.Many2one('account.account', 'Account')
    general_budget_id = fields.Many2one('account.budget.post', 'Budgetary Position', required=False)
    planned_amount = fields.Float(
        'Planned Amount', required=True, digits=0,
        help="Amount you plan to earn/spend. "
             "Record a positive amount if it is a revenue and a negative amount if it is a cost.")
    practical_amount = fields.Float(
        compute='_compute_practical_amount',
        string='Practical Amount',
        help="Account Amount (Amount really earned/spent.)",
        digits=0)
    is_above_budget = fields.Boolean(compute='_is_above_budget')

    # @api.depends('account_id', 'general_budget_id', 'analytic_account_id', 'date_from', 'date_to')
    @api.multi
    def _compute_practical_amount(self):
        for line in self:
            select = None
            where_clause_params = None
            acc_ids = line.general_budget_id.account_ids.ids
            date_to = line.date_to
            date_from = line.date_from
            if line.analytic_account_id.id:
                analytic_line_obj = self.env['account.analytic.line']
                domain = [('account_id', '=', line.analytic_account_id.id),
                          ('date', '>=', date_from),
                          ('date', '<=', date_to),
                          ]
                if acc_ids:
                    domain += [('general_account_id', 'in', acc_ids)]

                where_query = analytic_line_obj._where_calc(domain)
                analytic_line_obj._apply_ir_rules(where_query, 'read')
                from_clause, where_clause, where_clause_params = where_query.get_sql()
                select = "SELECT SUM(amount) from " + from_clause + " where " + where_clause
            elif line.general_budget_id or line.account_id:
                if line.general_budget_id:
                    filter_account = ('account_id', 'in', line.general_budget_id.account_ids.ids)
                else:
                    filter_account = ('account_id', '=', line.account_id.id)
                aml_obj = self.env['account.move.line']
                domain = [filter_account,
                          ('date', '>=', date_from),
                          ('date', '<=', date_to)
                          ]
                where_query = aml_obj._where_calc(domain)
                aml_obj._apply_ir_rules(where_query, 'read')
                from_clause, where_clause, where_clause_params = where_query.get_sql()
                select = "SELECT sum(credit)-sum(debit) from " + from_clause + " where " + where_clause

            if select:
                self.env.cr.execute(select, where_clause_params)
                practical_amount = self.env.cr.fetchone()[0] or 0.0
            else:
                practical_amount = 0
            line.practical_amount = practical_amount

    @api.constrains('general_budget_id', 'analytic_account_id', 'account_id')
    def _must_have_analytical_or_budgetary_or_account(self):
        if not self.analytic_account_id and not self.general_budget_id\
                and not self.account_id:
            raise ValidationError(
                _("You have to enter at least a [budgetary position or analytic account or account] on a budget line."))

    @api.multi
    def _is_above_budget(self):
        for line in self:
            if line.theoritical_amount >= 0:
                line.is_above_budget = line.practical_amount > line.theoritical_amount
            else:
                line.is_above_budget = line.practical_amount < line.theoritical_amount

    @api.model
    def _compute_line_name(self):
        #just in case someone opens the budget line in form view
        computed_name = self.crossovered_budget_id.name
        if self.analytic_account_id:
            computed_name += ' - ' + self.analytic_account_id.name
        elif self.general_budget_id:
            computed_name += ' - ' + self.general_budget_id.name
        elif self.account_id:
            computed_name += ' - ' + self.account_id.name
        self.name = computed_name

    @api.multi
    def action_open_budget_entries(self):
        if self.analytic_account_id:
            # if there is an analytic account, then the analytic items are loaded
            action = self.env['ir.actions.act_window'].for_xml_id('analytic', 'account_analytic_line_action_entries')
            action['domain'] = [('account_id', '=', self.analytic_account_id.id),
                                ('date', '>=', self.date_from),
                                ('date', '<=', self.date_to)
                                ]
            if self.general_budget_id:
                action['domain'] += [('general_account_id', 'in', self.general_budget_id.account_ids.ids)]
        else:
            # otherwise the journal entries booked on the accounts of (the budgetary postition or account id) are opened
            if self.general_budget_id:
                filter_account = ('account_id', 'in', self.general_budget_id.account_ids.ids)
            else:
                filter_account = ('account_id', '=', self.account_id.id)
            action = self.env['ir.actions.act_window'].for_xml_id('account', 'action_account_moves_all_a')
            action['domain'] = [filter_account,
                                ('date', '>=', self.date_from),
                                ('date', '<=', self.date_to)
                                ]
        return action

    @api.one
    @api.constrains('date_from', 'date_to')
    def _line_dates_between_budget_dates(self):
        budget_date_from = self.crossovered_budget_id.date_from
        budget_date_to = self.crossovered_budget_id.date_to
        if self.date_from:
            date_from = self.date_from
            if date_from < budget_date_from or date_from > budget_date_to:
                raise ValidationError(
                    _('"Start Date" of the budget line should be included in the Period of the budget'))

        if self.date_to:
            date_to = self.date_to
            if date_to < budget_date_from or date_to > budget_date_to:
                raise ValidationError(_('"End Date" of the budget line should be included in the Period of the budget'))


