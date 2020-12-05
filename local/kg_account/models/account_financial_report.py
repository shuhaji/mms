from odoo import models, fields, api


class KgAccountFinancialReport(models.Model):
    _inherit = "account.financial.report"
    _order = 'sequence'

    type = fields.Selection([
        ('sum', 'View'),
        ('accounts', 'Accounts'),
        ('account_type', 'Account Type'),
        ('account_group', 'Account Group'),
        ('account_report', 'Report Value'),
        ], 'Type', default='sum')

    account_group_ids = fields.Many2many(
        'account.group', 'account_account_financial_report_group', 'report_id',
        'account_group_id', 'Account Groups')

    is_total_income = fields.Boolean(
        default=False,
        string="Total Income (as Ratio divisor)",
        help="To Calculate Income Statement Ratio (as a divisor)")

    is_cf_init_balance = fields.Boolean(
        default=False,
        string="Is Cash Flow Initial Balance",
        help="Beginning Balance for Cash Flow Report")

    is_show_at_group_header = fields.Boolean(
        default=True,
        string="Show row data",
        help="Show row data on report (at the group header if has details)")
    is_show_total_at_bottom = fields.Boolean(
        default=False,
        string="Show Total at Bottom",
        help="Show total at the bottom of group")
    label_total_bottom = fields.Char(
        default=False,
        string="Label Total Bottom")
    is_show_border_top = fields.Boolean(
        default=False,
        string="Show Border Top",
        help="Show border top (for total amount)")
    is_show_border_bottom = fields.Boolean(
        default=False,
        string="Show Border Bottom",
        help="Show border bottom (for total amount)")
    reverse_balance_value = fields.Selection(
        [(-1, 'Reverse balance value (credit-debit)'), (1, 'Preserve balance value (debit-credit)')],
        'Reverse Balance Value',
        required=True, default=1)

    @api.multi
    def _parent_info(self):
        for rec in self:
            rec.parent_info = rec.parent_id.name or rec.name

    @api.multi
    def _grand_parent_info(self):
        for rec in self:
            rec.grand_parent_info = rec.parent_id.parent_id.name or rec.parent_id.name or rec.name

    parent_info = fields.Char(compute='_parent_info', string='Parent', store=False)
    grand_parent_info = fields.Char(compute='_grand_parent_info', string='Grand Parent', store=False)
