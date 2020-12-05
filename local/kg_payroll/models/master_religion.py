from odoo import models, fields


class EmpReligion(models.Model):
    _name = 'hr.religion'
    _rec_name = 'religion_name'

    religion_name = fields.Char('Religion Name',
                                help='Religion Name', required=True)

    active = fields.Boolean('Is Active',
                            help='Is Active or Archive',
                            default=True)

    create_uid = fields.Many2one('res.users', string='Created by', readonly=True)
    create_date = fields.Datetime(string='Created on', readonly=True)
    write_uid = fields.Many2one('res.users', string='Last Updated by', readonly=True)
    write_date = fields.Datetime(string='Last Updated on', readonly=True)

