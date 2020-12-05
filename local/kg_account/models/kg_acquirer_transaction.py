from datetime import datetime

from odoo import api, fields, models
from dateutil import parser


class KGAcquirerTransaction(models.Model):
    _name = 'kg.acquirer.transaction'
    _order = 'id desc'
        
    name = fields.Char()
    journal_id = fields.Many2one('account.journal', string='Journal',
                                 domain="[('is_bank_edc_credit_card', '=', True)]",
                                 index=True
                                 )
    company_id = fields.Many2one(
        'res.company', string='Company', store=True,
        readonly=True,
        default=lambda self: self.env['res.company']._company_default_get('kg.acquirer.transaction'),
        index=True
    )
    type = fields.Selection([
        (1, 'Payment'),
        (-1, 'Settlement'), ],

    )

    date = fields.Date(default=lambda self: self.payment_id.payment_date, index=True)
    # date = fields.Date(required=True, related='payment_id.payment_date', index=True)
    # date = fields.Date(required=True, compute='_get_payment_date', index=True)

    kg_issuer_type_id = fields.Many2one(
        'kg.issuer.type',
        'Issuer Type'
    )
    amount = fields.Float()  # original amount
    amount_applied = fields.Float()
    amount_remain = fields.Float()
    amount_transfer = fields.Float()  # amount paid (amount yg cair saat trx pencairan cc)

    settlement_ids = fields.One2many('kg.acquirer.transaction', 'apply_id', 'Trx Pencairan CC')

    payment_id = fields.Many2one('account.payment', 'Payment', ondelete='cascade')

    apply_id = fields.Many2one(
        'kg.acquirer.transaction',
        'Settlement For',
        domain="[('journal_id', '=', self.payment_id.journal_id.id), ('type', '=', 1), ('amount_remain', '>', 0)]",
        # domain=lambda self: [('amount_remain', '>', 0), ('type', '=', 1), ('id', 'not in', self.apply_id)]
    )
    apply_name = fields.Char(
        'Apply Name',
        compute='_get_apply_name',
        store=True
    )

    @api.multi
    def _get_apply_name(self):
        for rec in self:
            rec.apply_name = rec.define_apply_name(
                name=rec.apply_id.name if rec.apply_id else rec.name,
                kg_issuer_type_id=rec.kg_issuer_type_id)

    # applied CC Transaction Date
    apply_id_date = fields.Date(related='apply_id.date', string='Date', store=False)
    apply_id_amount_remain = fields.Float(related='apply_id.amount_remain', string='Amount Residual')
    apply_id_amount = fields.Float(related='apply_id.amount')

    _sql_constraints = [('payment_acquire_unique', 'unique (payment_id,apply_id)',
                         'Duplicate payment in transaction line not allowed !')]

    @api.multi
    @api.depends('date', 'kg_issuer_type_id')
    def name_get(self):
        result = []
        for rec in self:
            name = rec.define_apply_name(name=rec.name, kg_issuer_type_id=rec.kg_issuer_type_id, )
            result.append((rec.id, name))
        return result

    @api.model
    def define_apply_name(self, name, kg_issuer_type_id):
        issuer_name = kg_issuer_type_id.name.replace(' ', '') if kg_issuer_type_id.name else '999'
        record_name = name if name else ''
        name = record_name + ' | ' + issuer_name  # + ' - ' + datetime.strftime(parser.parse(rec.date), '%Y/%m/%d')
        return name

    @api.model
    def create(self, values):
        record = super(KGAcquirerTransaction, self).create(values)
        # for rec in self:
        if values.get('apply_id', None) is not None:
            # self.date = self.payment_id.payment_date
            record.set_info_based_on_apply()
            amount_transfer = values.get('amount_transfer', None)
            apply_id = values.get('apply_id', None)
            record.update_acquirer_transaction(0, amount_transfer, apply_id)

    @api.multi
    def write(self, values):
        for rec in self:
            prev_amount_transfer = rec.amount_transfer
            if rec.type == -1 and values.get('amount_transfer', None) is not None:
                # for settlement/pencairan, amount = -1 * amount yg di transfer
                values['amount'] = -rec.amount_transfer
                rec.update_acquirer_transaction(prev_amount_transfer, values.get('amount_transfer'), rec.apply_id.id)

        super(KGAcquirerTransaction, self).write(values)

    @api.multi
    def unlink(self):
        for rec in self:
            rec.update_acquirer_transaction(0, -rec.amount_transfer, rec.apply_id.id)
        super(KGAcquirerTransaction, self).unlink()

    @api.multi
    def set_info_based_on_apply(self):
        for rec in self:
            rec.journal_id = rec.apply_id.journal_id
            rec.type = -1
            rec.kg_issuer_type_id = rec.apply_id.kg_issuer_type_id
            issuer = str(rec.kg_issuer_type_id.id) if rec.kg_issuer_type_id.id else '999'
            rec.date = rec.payment_id.payment_date
            if rec.date:
                rec.name = datetime.strftime(parser.parse(rec.date), '%Y%m%d') + '/' + issuer

            # self.date = self.apply_id.date
            # as information of acquirer trx source
            # rec.amount = rec.apply_id.amount
            # for settlement/pencairan, amount = -1 * amount yg di transfer
            rec.amount = -rec.amount_transfer
            rec.amount_applied = 0
            # rec.amount_remain = rec.apply_id.amount_remain
            rec.amount_remain = 0

    @api.model
    def update_acquirer_transaction(self, prev_amount_transfer, amount_transfer, apply_id):
        new_amount = amount_transfer - prev_amount_transfer
        # for rec in self:
        if apply_id and new_amount != 0:
            self.env.cr.execute("""
                update kg_acquirer_transaction set amount_applied = amount_applied + %s
                 , amount_remain = amount_remain - %s
                where id = %s
            """, (new_amount, new_amount, apply_id))

    @api.onchange('amount_transfer')
    def onchange_amount_transfer(self):
        for rec in self:
            if rec.amount_transfer:
                if rec.amount_transfer > rec.apply_id.amount_remain:
                    warning = {
                        'title': 'Warning',
                        'message': 'Please input Amount less than Amount Residual.'
                        }
                    return {'value': {'amount_transfer': False}, 'warning': warning}

    @api.onchange('apply_id')
    def onchange_apply_id(self):
        for rec in self:
            rec.set_info_based_on_apply()
            rec.amount_transfer = rec.apply_id.amount_remain

        # filtered out already selected transaction (prevent double select for current payment)
        # get already selected cc/acquirer transaction on this payment (to be excluded)
        selected_apply_id = [data.apply_id.id for data in self.payment_id.acquirer_ids
                             if data and data.apply_id and data.apply_id.id]

        domain_apply_id = [('journal_id', '=', self.payment_id.journal_id.id), ('type', '=', 1), ('amount_remain', '>', 0)]
        if selected_apply_id:
            domain_apply_id.append(('id', 'not in', selected_apply_id))
        # domain = [('id', 'not in', available_ids), ('type', '=', 1), ('amount_remain', '>', 0)]
        return {'domain': {'apply_id': domain_apply_id}}




