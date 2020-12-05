# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, _


class KGPosCategory(models.Model):
    _inherit = "pos.category"

    pos_category_mapping_ids = fields.One2many('pos.category.mapping', 'pos_category_id', 'Department Mapping')


class KGPostCategoryMapping(models.Model):
    _name = "pos.category.mapping"

    pos_category_id = fields.Many2one('pos.category', 'POS Category', ondelete='cascade')
    pms_sub_department_id = fields.Char(string='PMS SubDepartment Id')
    department_id = fields.Many2one('hr.department', 'Department')
    company_id = fields.Many2one('res.company',
                                 'Company',
                                 help="Company Id",
                                 required=True,
                                 default=lambda self: self.env.user.company_id.id)

    keycard_encoder_id = fields.Many2one('keycard.encoder', 'Default Keycard Encoder')

