# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, SUPERUSER_ID, _


class MMSResPartner(models.Model):
    _inherit = 'res.partner'

    is_vlk = fields.Boolean(
        'No VLK',
        default=False,
    )

    vlk_id = fields.Integer(string='Nomor Sertifikasi')
    npwp_perusahaan = fields.Char(string='NPWP Perushaan')
    luas_lokasi = fields.Char(string='Luas Lokasi')
    lokasi = fields.Char(string='Lokasi 1 kecamatan')
    lokasi_2 = fields.Char(string='Lokasi 2 kabupaten')
    mr = fields.Char(string='MR')
    ktp_dirut = fields.Char(string='No KTP Direktur')
    nama_dirut = fields.Char(string='Nama Direktur')
    addres_dirut = fields.Char(string='Alamat Direktur')
    npwp_dirut = fields.Char(string='NPWP Direktur')
    contact_per = fields.Char(string='Kontak Person')
    telp_cp_1 = fields.Char(string='Telp Kontak Person 1')
    telp_cp_2 = fields.Char(string='Telp Kontak Person 2')


    # _sql_constraints = [
    #     ('contact_comp_unique', 'unique(pms_company_id, pms_contact_id)', 'Contact ID must be unique per Company!'),
    # ]
