# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Course(models.Model):
    _name = 'academic.course'
    _rec_name = 'name'

    _sql_constraints = [('vlk_booking_unique', 'unique (vlk_booking_id)',
                         'Duplicate number Vlk not allowed !')]

    @api.model
    def _get_default_number(self):
        return self.env['ir.sequence'].next_by_code('academic.course.number')

    number = fields.Char(string='Nomor', required=True, default=_get_default_number, track_visibility='onchange')

    vlk_booking_id = fields.Integer(string="Vlk Booking ID")

    name = fields.Many2one(string="Nama Auditee", comodel_name='res.company', required=False, )

    niu = fields.Char(string="Nomor Izin Usaha", required=False, )

    luas_usaha = fields.Float(string="Luas Usaha", required=False, )

    responsible = fields.Char(string="Penanggung Jawab", required=False, )

    address = fields.Char(string="Alamat", required=False, )

    distric = fields.Char(string="Kabupaten", required=False, )

    city = fields.Char(string="Provinsi", required=False, )

    ruang_lingkup = fields.Char(string="Ruang lingkup", required=False, )

    npwp = fields.Char(string="NPWP", required=False, )

    contact_person = fields.Text(string="No.Kontak", required=False, )




    # responsible_id = fields.Many2one(comodel_name="res.users",
    #                                  string="Responsible")
    # session_ids = fields.One2many(comodel_name="academic.session",
    #                               inverse_name="course_id",
    #                               string="Sessions", required=False,
    #                               ondelete="cascade")

