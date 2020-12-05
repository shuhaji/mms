from openerp import api, models, fields, _

class KGInvoiceCollectingWizard(models.TransientModel):
    _name = 'invoice.collecting.wizard'

    collecting_id = fields.Many2one(
        string='Collecting',
        comodel_name='invoice.collecting',
    )

    item_ids = fields.One2many(
        string='Line Items',
        comodel_name='invoice.collecting.wizard.items',
        inverse_name='wizard_id'
    )

    @api.model
    def default_get(self, fields):
        items = []
        collecting_ids = self.env['invoice.collecting'].browse(self._context.get('active_ids', []))

        if collecting_ids:
            used_invoices = self.env['invoice.collecting'].search([
                ('invoice_collecting_line_ids', '!=', False)
            ]).mapped('invoice_collecting_line_ids').mapped('invoice_id').mapped('id')

            invoices = self.env['account.invoice'].search([
                ('state','=','open'),
                ('type','=','out_invoice'),
                ('id', 'not in', used_invoices),
            ])

            for invoice in invoices:
                items.append((0, 0, {
                    'invoice_id': invoice.id,
                    'partner_id': invoice.partner_id.id,
                    'number': invoice.number,
                    'amount_total': invoice.amount_total,
                    'amount_total_temp': invoice.amount_total,
                    'residual': invoice.residual,
                    'residual_temp': invoice.residual,
                    'paid_invoice': invoice.amount_total - invoice.residual,
                }))

            res = super(KGInvoiceCollectingWizard, self).default_get(fields)
            res['item_ids'] = items
            res['collecting_id'] = collecting_ids.id 
            return res

    @api.multi
    def add_invoice_to_billing_lines(self):
        records = []
        for item in self.item_ids:
            if item.selectable:
                records.append({
                    'invoice_id': item.invoice_id.id,
                    'name': item.invoice_id.number,
                    'customer_id': item.invoice_id.partner_id.id,
                    'date_due': item.invoice_id.date_due,
                    'amount_total': item.amount_total,
                    'residual': item.residual,
                    'pay_invoice': item.paid_invoice
                })
        if records:
            for record in records:
                self.collecting_id.write({
                    'invoice_collecting_line_ids': [(0, 0, {
                        'invoice_collecting_id': self.collecting_id.id,
                        'invoice_id': record['invoice_id'],
                        'name': record['name'],
                        'customer_id': record['customer_id'],
                        'date_due': record['date_due'],
                        'amount_total': record['amount_total'],
                        'residual': record['residual'],
                    })]
                })
        return True

class KGInvoiceCollectingWizardLine(models.TransientModel):
    _name = 'invoice.collecting.wizard.items'

    selectable = fields.Boolean(string='Select Record')

    wizard_id = fields.Many2one(
        string='Wizard Invoice to Billing',
        comodel_name='invoice.collecting.wizard'
    )

    invoice_id = fields.Many2one(
        string='Billing',
        comodel_name='account.invoice',
    )

    partner_id = fields.Many2one(
        string='Customer',
        comodel_name='res.partner',
    )

    number = fields.Char(string='Invoice')

    amount_total = fields.Float(string='Total Invoice')

    amount_total_temp = fields.Float(
        string="Total Invoice",
        compute='set_amount_total_temp',
    )

    residual = fields.Float(string='Balance')

    residual_temp = fields.Float(
        string='Balance',
        compute='set_residual_temp',
    )

    paid_invoice = fields.Float(
        string='Paid Invoice',
        compute='_generate_pay_invoice'
    )

    @api.multi
    def _generate_pay_invoice(self):
        for wizard in self:
            wizard.paid_invoice = wizard.amount_total - wizard.residual

    @api.multi
    @api.depends('amount_total')
    def set_amount_total_temp(self):
        for line in self:
            if line.amount_total:
                line.amount_total_temp = line.amount_total
    
    @api.multi
    @api.depends('residual')
    def set_residual_temp(self):
        for line in self:
            if line.residual:
                line.residual_temp = line.residual
