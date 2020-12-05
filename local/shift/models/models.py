# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Shift(models.Model):
    _name = 'hr.shift'
    _rec_name = 'description'

    code = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc",_time store=True)
    description = fields.Text()
    description2 = fields.Text()
    start_time = fields.Float(required=True)  # , compute="_compute_time"
    end_time = fields.Float(required=True)  # , compute="_compute_time"
    # start_time = fields.Char(size=5)
    # end_time = fields.Char(size=5)

    department_id = fields.Many2one('hr.department', 'Department')
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
                                 required=True, readonly=True,
                                 default=lambda self: self.env['res.company']._company_default_get('hr.shift'))

    @api.onchange('department_id')
    def _onchange_department(self):
        self.parent_id = self.department_id.manager_id

    @api.multi
    @api.constrains('meal_time_line_ids')
    def check_time(self):
        line_position = 0
        end_time = 0
        if len(self) > 1:
            for line in self:
                if not (0.0 <= line.start_time <= 23.59):
                    raise ValidationError(_('Invalid meal time! \n You need to set time correctly'))

                if not (0.0 <= line.end_time <= 23.59):
                    raise ValidationError(_('Invalid meal time! \n You need to set time correctly'))

                # check if line.start is higher than line.end
                if line.end_time == 0.0:
                    end_time = 24
                    if line.start_time >= end_time:
                        raise ValidationError(_(
                            'Invalid meal time! \n You need to set meal time in sequence '
                            'and not overlapping each other!'))
                else:
                    if line.start >= line.end:
                        raise ValidationError(_(
                            'Invalid meal time! \n You need to set meal time in sequence '
                            'and not overlapping each other!'))

                # check if each line.end higher than each next line.start
                for index in range(len(self)):
                    if len(self) > index + 1:
                        if index >= line_position:
                            if line.end_time == 0.0:
                                end_time = 24
                                if end_time >= self[index + 1].start_time:
                                    raise ValidationError(_(
                                        'Invalid meal time! \n You need to set meal time in sequence '
                                        'and not overlapping each other!'))
                            else:
                                if line.end_time >= self[index + 1].start_time:
                                    raise ValidationError(_(
                                        'Invalid meal time! \n You need to set meal time in sequence '
                                        'and not overlapping each other!'))
                line_position += 1
        else:
            if not (0.0 <= self.start_time <= 23.59):
                raise ValidationError(_('Invalid meal time! \n You need to set time correctly'))

            if not (0.0 <= self.end_time <= 23.59):
                raise ValidationError(_('Invalid meal time! \n You need to set time correctly'))

            if self.end_time != 0.0:
                if self.start_time >= self.end_time:
                    raise ValidationError(_(
                        'Invalid meal time! \n You need to set meal time in sequence and not overlapping each other!'))

#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100
