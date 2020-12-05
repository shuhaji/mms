from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
from odoo.osv.expression import FALSE_DOMAIN


class KGWizardPosMealAllocation(models.TransientModel):
    _name = 'wizard.pos.meal.allocation'
    _title = "Meals Redeem"

    pos_category_id = fields.Many2one('pos.category', 'POS Categories')
    pms_sub_department_id = fields.Char(string='PMS SubDepartment Id')
    working_date = fields.Date(default=fields.Date.today)
    # guest_info = fields.Char(store=False, readonly=False)
    room_no = fields.Char()
    guest_name = fields.Char(compute='_get_guest_info', store=True)
    guest_status = fields.Char(compute='_get_guest_info')
    person = fields.Char(compute='_get_guest_info')
    arrival_date = fields.Date(compute='_get_guest_info')
    departure_date = fields.Date(compute='_get_guest_info')
    extra_bed = fields.Char(compute='_get_guest_info')
    card_info = fields.Text(compute='_get_guest_info')

    pms_reservation_id = fields.Integer()
    allocation_id = fields.Many2one('pos.meal.allocation')

    @api.onchange('pos_category_id')
    def _onchange_pos_category(self):
        if self.pos_category_id:
            for rec in self.pos_category_id.pos_category_mapping_ids:
                self.pms_sub_department_id = rec.pms_sub_department_id
                self.room_no = ''
                # self.isi_detail()

    def btn_isi_detail(self):
        for rec in self:
            outlet_allocation = self.env['pos.helpers'].get_meal_allocation(rec.working_date, rec.pms_reservation_id)
            pos_meal_allocation = self.env['pos.meal.allocation'].search([
                ('pos_category_id', '=', rec.pos_category_id.id),
                ('working_date', '=', rec.working_date),
                ('room_no', '=', rec.room_no),
            ])

            # existing_outlet_id = self.env['pos.meal.redeem'].search([
            #     ('allocation_id', '=', pos_meal_allocation.id),
            # ])
            # rec.outlet_ids = False
            existing_outlet_ids = []
            existing_outlet_ids.clear()
            existing_outlet_ids = self.env['pos.meal.redeem'].search_read([
                ('allocation_id', '=', pos_meal_allocation.id)
            ])

            # outlet_lines = self.outlet_list.filtered('manual')
            for outlet in outlet_allocation:
                # outlet_lines += outlet_lines.new(outlet)
                if outlet.get('SubdepartmentId') not in existing_outlet_ids:
                    # search pos_categories
                    pos_categories = self.env['pos.category.mapping'].search([
                        ('company_id.hotel_id', '=', outlet.get('HotelId')),
                        ('pms_sub_department_id', '=', outlet.get('SubdepartmentId')),
                    ])

                    existing_outlet_ids.append([0, 0, {
                        'allocation_id': pos_meal_allocation[0].id if pos_meal_allocation.id else pos_meal_allocation.id,
                        'pos_category_id': pos_categories[0].pos_category_id.id if pos_categories.id else pos_categories.id,
                        'pms_sub_department_id': outlet.get('SubdepartmentId'),
                        'allocation': outlet.get('Allocation'),
                        'redeem': 0,
                        'balance': outlet.get('Allocation'),
                        'source_type': 'direct',
                    }])

            if existing_outlet_ids:
                # rec.write({'outlet_ids': existing_outlet_ids})
                rec.outlet_ids = existing_outlet_ids

        return self._reopen_form()

    outlet_ids = fields.One2many(comodel_name='wizard.pos.meal.redeem',
                                 inverse_name='wizard_allocation_id', string='Outlet List')
                                 # default=_isi_detail)
    redeem_ids = fields.One2many(related='allocation_id.outlet_ids')

    click_redeem = fields.Boolean(default=False, store=False)

    @api.onchange('room_no')
    def _get_guest_info(self):
        if self.click_redeem:
            return
        if self.room_no and '--' not in self.room_no:
            return
        for rec in self:
            if rec.room_no and '--' in rec.room_no:
                guest_name = rec.room_no.split('--')[1].strip()
                guest_status = rec.room_no.split('--')[2].strip()
                person = (rec.room_no.split('--')[3].strip() + '/' + rec.room_no.split('--')[7].strip())
                arrival_date = datetime.strptime(rec.room_no.split('--')[4].strip()[:10], '%Y-%m-%d')
                departure_date = datetime.strptime(rec.room_no.split('--')[5].strip()[:10], '%Y-%m-%d')
                extra_bed = (rec.room_no.split('--')[6].strip()) \
                    if rec.room_no.split('--')[6].strip() == '0' \
                    else rec.room_no.split('--')[6].strip() + '/' + rec.room_no.split('--')[8].strip()
                room_no = rec.room_no.split('--')[0].strip()
                # room_no = rec.room_no
                pms_reservation_id = int(rec.room_no.split('--')[9].strip())
            else:
                guest_name = ""
                guest_status = ""
                person = ""
                arrival_date = False
                departure_date = False
                extra_bed = ""
                room_no = ""
                pms_reservation_id = 0

            rec.update({
                'guest_name': guest_name,
                'guest_status': guest_status,
                'person': person,
                'arrival_date': arrival_date,
                'departure_date': departure_date,
                'extra_bed': extra_bed,
                'room_no': room_no,
                'pms_reservation_id': pms_reservation_id,
            })

            outlet_allocation = self.env['pos.helpers'].get_meal_allocation(rec.working_date, pms_reservation_id)
            pos_meal_allocation = self.env['pos.meal.allocation'].search([
                ('pos_category_id', '=', rec.pos_category_id.id),
                ('working_date', '=', rec.working_date),
                ('room_no', '=', rec.room_no),
            ])

            rec.allocation_id = pos_meal_allocation.id

            rec.outlet_ids = False
            outlet_ids = []
            existing_outlet_ids = []
            existing_outlet_ids.clear()
            existing_outlet_ids = self.env['pos.meal.redeem'].search_read([
                ('allocation_id', '=', pos_meal_allocation.id)
            ])

            sub_dept_ids = []
            sum_outlet_ids = []
            i = 0
            for allocation in existing_outlet_ids:
                if int(allocation.get('pms_sub_department_id', 0)) not in sub_dept_ids:
                    sub_dept_ids.append(int(allocation.get('pms_sub_department_id', 0)))
                    sum_outlet_ids.append(allocation)

            for outlet in outlet_allocation:
                pos_categories = self.env['pos.category.mapping'].search([
                    ('company_id.hotel_id', '=', outlet.get('HotelId')),
                    ('pms_sub_department_id', '=', outlet.get('SubdepartmentId')),
                ])
                if outlet.get('SubdepartmentId') not in sub_dept_ids:
                    # search pos_categories
                    outlet_ids.append([0, 0, {
                        'allocation_id': False,
                        'pos_category_id': pos_categories[0].pos_category_id.id if pos_categories.id else pos_categories.id,
                        'pms_sub_department_id': outlet.get('SubdepartmentId'),
                        'allocation': outlet.get('Allocation'),
                        'redeem': 0,
                        'balance': outlet.get('Allocation'),
                        'source_type': 'direct',
                        # 'redeem_id': False,
                    }])
                else:
                    redeem_ids = self.env['pos.meal.redeem'].search_read([
                        ('allocation_id', '=', pos_meal_allocation.id),
                        ('pms_sub_department_id', '=', sum_outlet_ids[i]['pms_sub_department_id']),
                    ])
                    redeem = len(redeem_ids)
                    outlet_ids.append([0, 0, {
                        'allocation_id': sum_outlet_ids[i]['allocation_id'][0],
                        'pos_category_id': sum_outlet_ids[i]['pos_category_id'][0],
                        'pms_sub_department_id': sum_outlet_ids[i]['pms_sub_department_id'],
                        'allocation': sum_outlet_ids[i]['allocation'],
                        'redeem': redeem,
                        'balance': sum_outlet_ids[i]['allocation'] - redeem,
                        'source_type': sum_outlet_ids[i]['source_type'],
                        # 'redeem_id': existing_outlet_ids[i]['id'],
                    }])
                    i += 1

            if outlet_ids:
                rec.outlet_ids = outlet_ids

    @api.model
    def search_guest_info(self, *args, **kwargs):
        # TODO: get data from PMS
        working_date = kwargs.get('date')
        search = kwargs.get('search')
        guests = self.env['pos.helpers'].get_guest_info(working_date)
        # guests = [
        #     {"Nama": "Otto Clay", "Age": 25, "Country": 1, "Address": "Ap #897-1459 Quam Avenue", "Married": False},
        #     {"Nama": "Connor Johnston", "Age": 45, "Country": 2, "Address": "Ap #370-4647 Dis Av.", "Married": True},
        #     {"Nama": "Lacey Hess", "Age": 29, "Country": 3, "Address": "Ap #365-8835 Integer St.", "Married": False},
        #     {"Nama": "Timothy Henson", "Age": 56, "Country": 1, "Address": "911-5143 Luctus Ave", "Married": True},
        #     {"Nama": "Ramona Benton", "Age": 32, "Country": 3, "Address": "Ap #614-689 Vehicula Street",
        #      "Married": False}
        # ]
        result_guests = []
        for r in guests:
            if search.upper() in r['GuestName'].upper() or search == r['RoomNo']:
                result_guests.append(r)

        # raise UserError('abc')
        return result_guests

    def btn_set_redeem(self, vals):
        self.click_redeem = True

        # if self.pos_category_id:
        #     for rec in self.pos_category_id.pos_category_mapping_ids:
        #         self.pms_sub_department_id = rec.pms_sub_department_id

        values = {
            'pos_category_id': self.pos_category_id.id,
            'pms_sub_department_id': self.pms_sub_department_id,
            'working_date': self.working_date,
            'room_no': self.room_no,
            'outlet_ids': [],
            'pms_reservation_id': self.pms_reservation_id
        }

        meal_allocation = self.env['pos.meal.allocation'].search([
            ('pos_category_id', '=', self.pos_category_id.id),
            ('working_date', '=', self.working_date),
            ('room_no', '=', self.room_no),
        ])
        exists = False
        # allocation_id = False
        records = []
        for rec in self.outlet_ids:
            if rec.set_redeem:
                if meal_allocation.id:
                    exists = True
                    # if rec.redeem_id.id:
                    #     meal_allocation.write({
                    #         'outlet_ids': [(1, rec.redeem_id.id, {
                    #             'allocation_id': rec.allocation_id.id,
                    #             'pos_category_id': rec.pos_category_id.id,
                    #             'pms_sub_department_id': rec.pms_sub_department_id,
                    #             'allocation': rec.allocation,
                    #             'redeem': rec.redeem + 1,
                    #             'source_type': 'direct'
                    #         })]
                    #     })
                    # else:
                    meal_allocation.write({
                        'outlet_ids': [(0, 0, {
                            'allocation_id': False,
                            'pos_category_id': rec.pos_category_id.id,
                            'pms_sub_department_id': rec.pms_sub_department_id,
                            'allocation': rec.allocation,
                            'redeem': 1,
                            'source_type': 'direct',
                        })]
                    })
                    rec.redeem += 1
                else:
                    vals = {
                        'allocation_id': False,
                        'pos_category_id': rec.pos_category_id.id,
                        'pms_sub_department_id': rec.pms_sub_department_id,
                        'allocation': rec.allocation,
                        'redeem': 1,
                        'source_type': 'direct'
                    }
                    records.append(vals)
                    values['outlet_ids'].append((0, 0, vals))
                    rec.redeem += 1

        if not exists:
            meal_allocation.create(values)

        self.click_redeem = False

        return self._reopen_form()

    def btn_redeem_info(self):
        allocation_id = False
        for rec in self.outlet_ids:
            allocation_id = rec.allocation_id.id

        # view_id = self.env['ir.ui.view'].search(
        #     [('name', '=', 'pos.meal.redeem.info.form'), ('type', '=', 'form')])
        view_id = self.env.ref('kg_pos.pos_meal_redeem_info_form')
        return {
            'name': _("Redeem Info "),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.meal.allocation',
            'view_id': view_id.id,
            'target': 'new',
            'context': {'default_allocation_id': allocation_id, }
        }

    @api.multi
    def _reopen_form(self):
        self.ensure_one()
        # return {"type": "ir.actions.do_nothing"}

        # jika view tampil sbg modal:
        target = 'new'
        # jika view sbg form biasa (bukan modal dialog)
        # target = 'inline'

        view_id = self.env['ir.ui.view'].search(
            [('model', '=', self._name), ('type', '=', 'form')])
        return {
            'context': self.env.context,
            'view_id': view_id.id,
            # 'name': "KG Report - Sample",
            "name": self._title,
            'type': 'ir.actions.act_window',
            'res_model': self._name,  # this model
            'res_id': self.id,  # the current wizard record
            'view_type': 'form',
            'view_mode': 'form',
            'target': target}


class KGWizardPosMealRedeem(models.TransientModel):
    _name = 'wizard.pos.meal.redeem'

    set_redeem = fields.Boolean(string=" ")
    wizard_allocation_id = fields.Many2one('wizard.pos.meal.allocation')
    allocation_id = fields.Many2one('pos.meal.allocation')
    pos_category_id = fields.Many2one('pos.category', 'POS Categories')
    pms_sub_department_id = fields.Char(string='PMS SubDepartment Id')
    allocation = fields.Integer()
    redeem = fields.Integer()
    balance = fields.Integer(compute='get_allocation_balance', readonly=True)
    source_type = fields.Selection([
        ("direct", "Direct"),
        ("encoder", "Encoder"),
    ])
    # redeem_id = fields.Many2one('pos.meal.redeem')

    @api.depends('redeem')
    def get_allocation_balance(self):
        for rec in self:
            rec.balance = rec.allocation - rec.redeem

    @api.onchange('set_redeem')
    def _onchange_pos_category(self):
        if self.set_redeem and self.allocation == self.redeem:
            self.set_redeem = False
            raise UserError("Redeem has reached limit.")


class KGPosMealAllocation(models.Model):
    _name = 'pos.meal.allocation'

    pos_category_id = fields.Many2one('pos.category', 'POS Categories')
    pms_sub_department_id = fields.Char(string='PMS SubDepartment Id', readonly=True)
    working_date = fields.Date(default=fields.Date.today)
    room_no = fields.Char(readonly=False)
    outlet_ids = fields.One2many('pos.meal.redeem',
                                 'allocation_id', string='Outlet List')
    pms_reservation_id = fields.Integer()


class KGPosMealRedeem(models.Model):
    _name = 'pos.meal.redeem'

    allocation_id = fields.Many2one('pos.meal.allocation')
    pos_category_id = fields.Many2one('pos.category', 'POS Categories')
    pms_sub_department_id = fields.Char(string='PMS SubDepartment Id')
    allocation = fields.Integer()
    redeem = fields.Integer()
    balance = fields.Integer(compute='get_allocation_balance', readonly=True)
    source_type = fields.Selection([
        ("direct", "Direct"),
        ("encoder", "Encoder"),
    ])

    room_no = fields.Char(related='allocation_id.room_no')
    outlet = fields.Char(related='allocation_id.pos_category_id.name')
    redeem_location = fields.Char(related='pos_category_id.name')
    created = fields.Char(compute='_get_timestamp')
    user = fields.Char(related='create_uid.name')

    def _get_timestamp(self):
        for rec in self:
            rec.created = rec.create_date + ' By ' + rec.user

    @api.depends('redeem')
    def get_allocation_balance(self):
        for rec in self:
            rec.balance = rec.allocation - rec.redeem




