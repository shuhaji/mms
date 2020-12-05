# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Pelaksana(models.Model):
    _name = 'pelaksana'

    description = fields.Text(string="Description", required=False, )

    @api.model
    def _get_default_number(self):
        return self.env['ir.sequence'].next_by_code('pelaksana.number')

    name = fields.Char(string='Number', required=True,
                       default=_get_default_number,
                       track_visibility='onchange')
    auditor = fields.Char('Auditor')

    jabatan = fields.Char(string="Jabatan Auditor", required=False, )

    mulai_tugas = fields.Date(string="Tanggal Mulai Tugas", required=False, )

    akhir_tugas = fields.Date(string="Tanggal Akhir Tugas", required=False, )

    tanggal = fields.Date(string="Tanggal", required=False, )


    # responsible_id = fields.Many2one(comodel_name="res.users",
    #                                  string="Responsible")
    # session_ids = fields.One2many(comodel_name="academic.session",
    #                               inverse_name="course_id",
    #                               string="Sessions", required=False,
    #                               ondelete="cascade")

