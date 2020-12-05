# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DataSertifikasi(models.Model):
    _name = 'data.sertifikasi'
    _rec_name = 'name'

    # _sql_constraints = [('vlk_booking_unique', 'unique (vlk_booking_id)',
    #                      'Duplicate number Vlk not allowed !')]

    # @api.model
    # def _get_default_number(self):
    #     return self.env['ir.sequence'].next_by_code('academic.course.number')

    name = fields.Char('Auditee')
    vlk_id = fields.Integer(string='No VLK')

    category_vlk = fields.Char(string="Code")

    durasi_vlk = fields.Char(string="Lama VLK")

    masa_awal_sertifikasi = fields.Date(string="Awal Sertifikasi")

    masa_akhir_sertifikasi = fields.Date(string="Akhir Sertifikasi")

    penilikan_1 = fields.Date(string="Penilikan 1")

    penilikan_2 = fields.Date(string="Penilikan 2")

    penilikan_3 = fields.Date(string="Penilikan 3")

    penilikan_4 = fields.Date(string="Penilikan 4")

    penilikan_5 = fields.Date(string="Penilikan 5")

    Status_vlk = fields.Boolean(string="Status")

    ts = fields.Date(string="TS")


    # responsible_id = fields.Many2one(comodel_name="res.users",
    #                                  string="Responsible")
    # session_ids = fields.One2many(comodel_name="academic.session",
    #                               inverse_name="course_id",
    #                               string="Sessions", required=False,
    #                               ondelete="cascade")

