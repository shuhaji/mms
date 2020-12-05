from odoo import models, fields, api, _
from odoo.exceptions import UserError


class KGBanquetProposal(models.Model):
    _name = 'banquet.proposal'
    # _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherit = ['mail.thread']
    _description = "Banquet Proposal"

    name = fields.Char(string='Proposal No', copy=False, readonly=True)
    contract_no = fields.Char(string='Contract No', readonly=True)
    remark = fields.Char(string='Remark')
    state = fields.Selection([('proposed', 'Proposed'), ('contract', 'Contract'), ('signed', 'Signed'), ('release', 'Released')],
                             readonly=True, default='proposed', string="Status"
                             , track_visibility='onchange')

    reservation_ids = fields.One2many(
        'banquet.reservation', 'proposal_id',
        string="Reservation", track_visibility='onchange',
        )
    company_id = fields.Many2one('res.company', related='reservation_ids.company_id')
    partner_id = fields.Many2one('res.partner', related='reservation_ids.partner_id')

    allow_edit = fields.Boolean(default=True, compute='set_allow_edit', store=False)

    @api.multi
    @api.depends('state')
    def set_allow_edit(self):
        for record in self:
            if record.state in ['proposed']:
                record.allow_edit = True
            else:
                record.allow_edit = False

    @api.multi
    def copy(self, default=None):
        default = dict(default or {})
        self.ensure_one()
        default.update({
            'state': 'proposed',
            'name': self.env['ir.sequence'].next_by_code('banquet.proposal.name'),
        })
        return super(KGBanquetProposal, self).copy(default)

    # @api.one
    # def button_draft(self):
    #     self.state = 'draft'
    #     self.contract_no = None
    #     for res_id in self.reservation_ids:
    #         res_id.state = 'proposal'

    @api.one
    def button_proposed(self):
        self.state = 'proposed'
        self.contract_no = None
        for res_id in self.reservation_ids:
            res_id.state = 'proposal'

    @api.one
    def button_contract(self):
        if self.state == 'proposed':
            self.state = 'contract'
            self.contract_no = self.env['ir.sequence'].next_by_code('banquet.proposal.contract')
            for res_id in self.reservation_ids:
                if res_id.state == 'proposal':
                    res_id.state = 'contract'
                else:
                    raise UserError('Please check reservation flow status')
        else:
            raise UserError('Please check proposal status')

    @api.one
    def button_signed(self):
        if self.state == 'contract':
            self.state = 'signed'
            for res_id in self.reservation_ids:
                if res_id.state == 'contract':
                    res_id.state = 'signed'
                else:
                    raise UserError('Please check reservation flow status')
        else:
            raise UserError('Please check proposal status')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('banquet.proposal.name')
        # important, agar field state berubah jadi proposal, pastikan field state di reservation TIDAK READ ONLY
        if not vals.get('reservation_ids', False):
            #     for record in vals['reservation_ids']:
            #         if self.env['banquet.reservation'].browse(record[0]) == 6:
            #             reservations = self.env['banquet.reservation'].browse(record[2])
            #             # if any(res.partner_id.id != reservations[0].partner_id.id for res in reservations):
            #             #     raise UserError(_("Banquet Proposal can't be saved for different customer."))
            #             for res in reservations:
            #                 if res.state == 'draft':
            #                     res.state = 'proposal'
            # else:
            raise UserError(_("Reservations can not  be empty !"))

        res = super(KGBanquetProposal, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        old_reservation_ids = self.reservation_ids.ids
        # important, agar field state berubah jadi proposal, pastikan field state di reservation TIDAK READ ONLY

        res = super(KGBanquetProposal, self).write(vals)

        if not self.reservation_ids:
            raise UserError(_("Reservations can not  be empty !"))

        deleted_ids = [reservation_id for reservation_id in old_reservation_ids
                       if reservation_id not in self.reservation_ids.ids]
        if deleted_ids:
            self.env['banquet.reservation'].search([('id', 'in', deleted_ids)]).write({
                'state': 'draft',
            })

        return res

    @api.multi
    def unlink(self):
        # reservation = self.env['banquet.reservation']
        for proposal in self:
            if proposal.state != 'proposed':
                raise UserError(_('You cannot delete a banquet proposal which is not in proposed state.'))
            else:
                if proposal.reservation_ids:
                    # reservation_unlink = reservation.search([('proposal_id', '=', proposal.ids)])
                    for rec in proposal.reservation_ids:
                        if rec.state in ('draft', 'proposal'):
                            rec.state = 'draft'
                            # rec.write({'state': 'draft'})
                        else:
                            raise UserError(_('You cannot delete proposal when some reservation not in proposal state.'))

        return super(KGBanquetProposal, self).unlink()

    @api.onchange('reservation_ids')
    def onchange_reservation_ids(self):
        if self.reservation_ids:
            partner_ids = [res.partner_id.id for res in self.reservation_ids]
            check_multi_partner = list(set(partner_ids))
            if len(check_multi_partner) > 1:
                raise UserError(_('Reservations must be from the same customer!'))

        for old_res in self._origin.reservation_ids:
            # if old_res.state != 'proposal':
            #     raise UserError(_('You cannot delete a reservation which is not in proposal state.'))
            if old_res.state in ('checkout', 'release'):
                raise UserError(_('You cannot remove a reservation which is in checkout or release state.'))

        for res in self.reservation_ids:
            if res.state == 'draft':
                res.proposal_id = self
                res.state = 'proposal'

    @api.multi
    def action_auto_release(self):
        proposal_ids = self.env['banquet.proposal'].sudo().search([
            ('state', 'in', ['proposed', 'contract', 'signed']),
        ])
        if proposal_ids:
            for proposal in proposal_ids:
                if proposal.reservation_ids:
                    not_release = 0
                    for rec in proposal.reservation_ids:
                        if not rec.state == 'release':
                            not_release += 1
                    if not_release == 0:
                        proposal.write({'state': 'release'})

    # def set_domain_for_reservation_ids(self):
    #     domain_proposal_id = [('state', '=', 'draft'), ('proposal_id', '=', None)]
    #     if self.partner_id:
    #         domain_proposal_id.append(('partner_id', '=', self.partner_id.id))
    #     # if self.reservation_ids:
    #     #     selected_ids = [res.proposal_id.id for res in self.reservation_ids if res.proposal_id]
    #     #     domain_proposal_id.append(('id', 'not in', selected_ids))
    #     return {'domain': {
    #         'reservation_ids': domain_proposal_id
    #     }}
