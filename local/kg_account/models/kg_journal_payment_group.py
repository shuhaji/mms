# Copyright 2013 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class KgJournalPaymentGroup(models.Model):
    _name = 'journal.payment.group'

    pms_payment_type = fields.Char('PMS Payment Type',
                                help='Type')

    name = fields.Char('Payment Group Name',
                                help='Name')

    short_name = fields.Char('Short Name',
                                help='Short Name')

    row_order = fields.Integer('Row Order',
                               help='PMS Payment Row Order')

    row_group = fields.Char('Row Group',
                                help="PMS Payment Row Order")

    active = fields.Boolean('Is Active',
                            help='Is Active or Archive',
                            default=1)

