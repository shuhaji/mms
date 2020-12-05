# -*- coding: utf-8 -*-

from odoo import models, fields, api


class TugasTim(models.Model):
    _name = 'tugas.tim'
    _rec_name = 'name'

    @api.model
    def _get_default_number(self):
        return self.env['ir.sequence'].next_by_code('pelaksana.number')

    name = fields.Char(string='Number', required=True,
                       default=_get_default_number,
                       track_visibility='onchange')

    auditor_second = fields.Char(string="Auditor Kedua", required=False, )

    auditor_third = fields.Char(string="Auditro Ketiga", required=False, )

    tanggal = fields.Date(string="Luas Usaha", required=False, )





    # responsible_id = fields.Many2one(comodel_name="res.users",
    #                                  string="Responsible")
    # session_ids = fields.One2many(comodel_name="academic.session",
    #                               inverse_name="course_id",
    #                               string="Sessions", required=False,
    #                               ondelete="cascade")

