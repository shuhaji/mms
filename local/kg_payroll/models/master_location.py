# Copyright 2013 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class EmpWorkLocation(models.Model):
    _name = 'hr.location'
    _rec_name = 'location_name'

    location_name = fields.Char('Location Name',
                            help='Location Name', required=True)

    location_code = fields.Char('Location Code',
                            help='Location Code', required=True)

    location_address = fields.Text('Location Address',
                            help='Location Address')

    active = fields.Boolean('Is Active',
                            help='Is Active or Archive',
                            default=True)

    company_id = fields.Many2one('res.company',
                                 'Company',
                                 help="Company Id")

    create_uid = fields.Many2one('res.users', string='Created by', readonly=True)
    create_date = fields.Datetime(string='Created on', readonly=True)
    write_uid = fields.Many2one('res.users', string='Last Updated by', readonly=True)
    write_date = fields.Datetime(string='Last Updated on', readonly=True)

