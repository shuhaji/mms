# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HasilPenilaiaan(models.Model):
    _name = 'hasil.penilaiaan'


    @api.model
    def _get_default_number(self):
        return self.env['ir.sequence'].next_by_code('penilaiaan.number')

    number = fields.Char(string='Number', required=True,
                       default=_get_default_number,
                       track_visibility='onchange')
    name = fields.Char('Auditee')

    nilai_memenuhi = fields.Boolean(string="Nilai Memenuhi", required=False, )

    nilai_predikat = fields.Char(string="Nilai Predikat", required=False, )

    kesimpulan = fields.Boolean(string="Kesimpulan Penilaiaan", required=False, )

    tanggal = fields.Date(string="Tanggal", required=False, )


    # responsible_id = fields.Many2one(comodel_name="res.users",
    #                                  string="Responsible")
    # session_ids = fields.One2many(comodel_name="academic.session",
    #                               inverse_name="course_id",
    #                               string="Sessions", required=False,
    #                               ondelete="cascade")

