# -*- coding: utf-8 -*-

from odoo import models, fields, api


class KeputusanSertifikasi(models.Model):
    _name = 'keputusan.sertifikasi'


    @api.model
    def _get_default_number(self):
        return self.env['ir.sequence'].next_by_code('keputusan.sertifikasi')

    number = fields.Char(string='Number', required=True,
                       default=_get_default_number,
                       track_visibility='onchange')
    name = fields.Char('Auditee')

    nomor_vlk = fields.Many2one(comodel_name="academic.course",
                                string="Nomor VLK", required=True, )

    tanggal_awal_sertifikat = fields.Date(string="Tanggal Awal Berlaku Sertifikat", required=False, )

    tanggal_berakhirnya_sertifikat = fields.Date(string="Tanggal Berakahirnya Sertifikat", required=False, )

    tanggal = fields.Date(string="Tanggal", required=False, )


    # responsible_id = fields.Many2one(comodel_name="res.users",
    #                                  string="Responsible")
    # session_ids = fields.One2many(comodel_name="academic.session",
    #                               inverse_name="course_id",
    #                               string="Sessions", required=False,
    #                               ondelete="cascade")

