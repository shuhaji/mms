# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, SUPERUSER_ID, _


class KGAccountJournal(models.Model):
    _inherit = 'account.journal'

    is_issuer_bank = fields.Boolean(
        'Is issuer bank',
        default=False,
    )

    is_department_expense = fields.Boolean(
        'Is department expense',
        default=False,
    )

    is_officer_check = fields.Boolean(
        'Is officer check',
        default=False,
    )

    is_city_ledger = fields.Boolean(
        'Is city ledger',
        default=False,
    )

    is_advance_payment = fields.Boolean(
        'Is advance payment',
        default=False,
    )

    # field ini tidak dipakai lagi. krn issuer type bisa utk general/lintas EDC
    # issuer_type_ids = fields.Many2many(
    #     'kg.issuer.type',
    #     'journal_bank_id',
    #     'Issuer Type',
    # )

    is_charge_room = fields.Boolean(
        'Is charge to room',
        defalt=False,
    )

    split_payment = fields.Boolean(
        'Split Payment',
        default=False,
    )

    is_point = fields.Boolean(
        'Is Point',
        default=False,
    )

    is_bank_edc_credit_card = fields.Boolean(
        'Is Acquirer (EDC CC, Cash Tracking)',
        default=False,
    )

    journal_payment_group_id = fields.Many2one(
        'journal.payment.group',
        string='Journal Payment No')

    is_voucher = fields.Boolean(
        'Is Voucher',
        default=False,
    )

    is_payroll = fields.Boolean(
        default=False
    )
