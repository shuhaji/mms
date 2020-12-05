# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PermohonanPenilaian(models.Model):
    _name = 'permohonan.penilaian'
    _rec_name = 'name'

    description = fields.Text(string="Description", required=False, )

    @api.model
    def _get_default_number(self):
        return self.env['ir.sequence'].next_by_code('permohonan.penilaian.number')

    name = fields.Char(string='Number', required=True,
                       default=_get_default_number,
                       track_visibility='onchange')
    auditee = fields.Many2one('academic.course')

    status_nilai = fields.Char(string="Status Penilaian", required=False, )

    kelengkapan_admini = fields.Char(string="Kelengkapan Administrasi", required=False, )

    kesesuaian_rl = fields.Float(string="Kesesuaian Dengan Ruang Lingkup", required=False, )

    legalitas = fields.Char(string="Legalitas Perusahaan", required=False, )

    kesesuaian_up = fields.Char(string="Kesesuaian Unit Pengelola", required=False, )

    masa_izin = fields.Date(string="Masa Izin Pengelolaan", required=False, )

    rekomendasi_hasil = fields.Char(string="Rekomendasi Hasil Kajian", required=False, )

    tanggal = fields.Date(string="Tanggal", required=False, )


    # responsible_id = fields.Many2one(comodel_name="res.users",
    #                                  string="Responsible")
    # session_ids = fields.One2many(comodel_name="academic.session",
    #                               inverse_name="course_id",
    #                               string="Sessions", required=False,
    #                               ondelete="cascade")

