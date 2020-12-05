# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from datetime import datetime, date, time
from odoo.exceptions import UserError, ValidationError

class KGPOSMealTime(models.Model):
    _name = 'meal.time'

    name = fields.Char(
        'Meal Time',
        required=True,
    )

    meal_time_line_ids = fields.One2many(
        'meal.time.line',
        'meal_time_id',
        'Meal Time Line'
    )

    meal_time_line_id = fields.Many2one(
        'meal.time.line',
        'Selected Meal Time Line',
        compute='set_meal_time_line_id',
    )

    @api.multi
    @api.depends('meal_time_line_ids')
    def set_meal_time_line_id(self):
        for meal_time in self:
            decimal_point = 0
            for line in meal_time.meal_time_line_ids:
                current_time = fields.Datetime.now()
                str_time = datetime.strptime(str(current_time),'%Y-%m-%d %H:%M:%S')
                current_hour = str_time.hour
                current_minute = str_time.minute
                if current_minute > 0:
                    if len(str(current_minute)) >= 1:
                        decimal_point = 10 ** len(str(current_minute))
                        valid_hour = current_hour + (current_minute / decimal_point)
                else:
                    valid_hour = current_hour

                if line.start <= valid_hour <= line.end:
                    meal_time.meal_time_line_id = line

    @api.multi
    @api.constrains('meal_time_line_ids')
    def check_time(self):
        line_position = 0
        end_time = 0
        if len(self.meal_time_line_ids) > 1:
            for line in self.meal_time_line_ids:
                if not (0.0 <= line.start <= 23.59):
                    raise ValidationError(_('Invalid meal time! \n You need to set time correctly'))

                if not (0.0 <= line.end <= 23.59):
                    raise ValidationError(_('Invalid meal time! \n You need to set time correctly'))

                #check if line.start is higher than line.end
                if line.end == 0.0:
                    end_time = 24
                    if line.start >= end_time:
                        raise ValidationError(_('Invalid meal time! \n You need to set meal time in sequence and not overlapping each other!'))
                else:
                    if line.start >= line.end:
                        raise ValidationError(_('Invalid meal time! \n You need to set meal time in sequence and not overlapping each other!'))

                #check if each line.end higher than each next line.start
                for index in range(len(self.meal_time_line_ids)):
                    if len(self.meal_time_line_ids) > index + 1:
                        if index >= line_position:
                            if line.end == 0.0:
                                end_time = 24
                                if end_time >= self.meal_time_line_ids[index + 1].start:
                                    raise ValidationError(_('Invalid meal time! \n You need to set meal time in sequence and not overlapping each other!'))
                            else:
                                if line.end >= self.meal_time_line_ids[index + 1].start:
                                    raise ValidationError(_('Invalid meal time! \n You need to set meal time in sequence and not overlapping each other!'))
                line_position += 1
        else:
            if not (0.0 <= self.meal_time_line_ids.start <= 23.59):
                raise ValidationError(_('Invalid meal time! \n You need to set time correctly'))

            if not (0.0 <= self.meal_time_line_ids.end <= 23.59):
                raise ValidationError(_('Invalid meal time! \n You need to set time correctly'))

            if self.meal_time_line_ids.end != 0.0:
                if self.meal_time_line_ids.start >= self.meal_time_line_ids.end:
                    raise ValidationError(_('Invalid meal time! \n You need to set meal time in sequence and not overlapping each other!'))



class KGPOSMealTimeLine(models.Model):
    _name = 'meal.time.line'

    name = fields.Char(
        'Name',
        related='meal_type',
    )

    meal_type = fields.Char(
        'Meal Type',
        required=True,
    )

    start = fields.Float(
        'Start',
        required=True,
    )

    end = fields.Float(
        'End',
        required=True,
    )

    meal_time_id = fields.Many2one(
        'meal.time',
        'Meal Time',
    )
