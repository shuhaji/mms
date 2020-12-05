from odoo import api, fields, models, tools, SUPERUSER_ID, _

REGION = [
    ('jakarta', 'Jakarta'),
    ('bali', 'Bali'),
    ('surabaya', 'Surabaya'),
]


class KGResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    def _get_default_admin_fee_account_id(self):
        return self.env.user.company_id.admin_fee_account_id

    region_name = fields.Selection(REGION, 'Region', required=True, default='jakarta')
    guest_ledger_account_id = fields.Many2one(
        'account.account',
        'Default Guest Ledger Account')
    close_advance_deposit_account_id = fields.Many2one(
        'account.account',
        'Close Advance Deposit Account')

    nopd_code = fields.Char("NOPD Hotel Code (for Tax Online)", default='')

    admin_fee_account_id = fields.Many2one(
        'account.account',
        'Default Admin Fee Account')

    base_url_iot_api = fields.Char("Base URL IoT API")

    @api.multi
    def set_values(self):
        super(KGResCompany, self).set_values()
        if self.admin_fee_account_id:
            self.sudo().env.user.company_id.admin_fee_account_id = self.admin_fee_account_id

