# Copyright 2013 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class KgVoucher(models.Model):
    _name = 'kg.voucher'

    name = fields.Char('Voucher Name',
                       help='Voucher Name',
                       required=True)

    company_id = fields.Many2one('res.company',
                                 'Company',
                                 help="Company Id",
                                 required=True,
                                 default=lambda self: self.env.user.company_id.id)

    is_external = fields.Boolean('Is External',
                                 help='Is External or Internal',
                                 default=0)

    start_date = fields.Date('Start Date',
                             help="Start Date",
                             required=True)

    end_date = fields.Date('End Date',
                           help='End Date',
                           required=True)

    is_open_amount = fields.Boolean('Is Open Amount',
                                    help='Is open amount',
                                    default=1)

    amount = fields.Integer('Amount',
                            help='Amount')

    # TODO: tambah filter domain hanya tampilkan company aja (contact di hide)
    partner_id = fields.Many2one('res.partner',
                                 'Partner',
                                 help="Partner Id")

    department_id = fields.Many2one('hr.department',
                                    'Department',
                                    help="Department Id")

    expense_account_id = fields.Many2one('account.account',
                                         'Expense Account',
                                         help="Expense Account Id")

    description = fields.Text('Description',
                              help='Description')

    voucher_pms_id = fields.Char(help="Id voucher in PMS")

    active = fields.Boolean('Is Active',
                            help='Is Active',
                            default=True)

