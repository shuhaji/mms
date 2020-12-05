# -*- coding: utf-8 -*-

from odoo import models, fields, api

class session(models.Model):

    _name = 'academic.session'

    name = fields.Char("Name", required=True)

    course_id = fields.Many2one(comodel_name="academic.course",
        string="Course", required=True, )
    instructor_id = fields.Many2one(comodel_name="res.partner",
        string="Instructor", required=True, )
    start_date = fields.Date(string="Start Date", required=False, )
    duration = fields.Integer(string="Duration", required=False, )
    seats = fields.Integer(string="Seats", required=False, )
    active = fields.Boolean(string="Active", )
    attendee_ids = fields.One2many(comodel_name="academic.attendee",
                                   inverse_name="session_id",
                                   string="Attendees",
                                   required=False, )
    taken_seats = fields.Float(compute="_calc_taken_seats",
                               string="Taken Seat", required=False, )

    @api.depends('attendee_ids', 'seats')
    def _calc_taken_seats(self):
        for rec in self:
            if rec.seats > 0:
                rec.taken_seats = 100.0 * len(rec.attendee_ids) / rec.seats
            else:
                rec.taken_seats = 0.0


