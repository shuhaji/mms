# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DataAuditor(models.Model):
    _name = 'data.auditor'
    _rec_name = 'name'

    # _sql_constraints = [('vlk_booking_unique', 'unique (vlk_booking_id)',
    #                      'Duplicate number Vlk not allowed !')]

    # @api.model
    # def _get_default_number(self):
    #     return self.env['ir.sequence'].next_by_code('academic.course.number')

    name = fields.Char('Auditor')
    auditor_id = fields.Integer(string='No Auditor')

    addres = fields.Char(string="Alamat")

    tempat_lahir = fields.Char(string="Tempat Lahir")

    tgl_lahir = fields.Date(string="Tanggal Lahir")

    agama = fields.Char(string="agama")

    gender = fields.Char(string="Jenis Kelamin")

    ktp = fields.Char(string="No KTP")

    telp = fields.Char(string="No Telepon/HP")

    status = fields.Char(string="Status")

    awal_vlk = fields.Date(string="Awal Sertifikat VLK")

    akhir_vlk = fields.Date(string="Akhir Sertifikat VLK")

    awal_phpl = fields.Date(string="Awal Sertifikat PHPL Ekologi")

    akhir_phpl = fields.Date(string="Akhir Sertifikat PHPL Ekologi")

    awal_phpl_prod = fields.Date(string="Awal Sertifikat PHPL Produksi")

    akhir_phpl_prod = fields.Date(string="Akhir Sertifikat PHPL Produksi")

    # responsible_id = fields.Many2one(comodel_name="res.users",
    #                                  string="Responsible")
    # session_ids = fields.One2many(comodel_name="academic.session",
    #                               inverse_name="course_id",
    #                               string="Sessions", required=False,
    #                               ondelete="cascade")

