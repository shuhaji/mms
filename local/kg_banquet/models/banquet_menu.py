from odoo import models, fields


class BanquetMenu(models.Model):
    _name = 'banquet.menu'
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name')
    event_menu_id = fields.Many2one('banquet.event.menu', string="Event Menu ID")
    desc = fields.Char(string='Description')
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id.id)
    product_ids = fields.Many2many(
        'product.product',
        'banquet_menu_product_rel',
        'menu_id',
        'product_id',
        string='Product List',
        domain="[('is_banquet', '=', True), ('item_type', '=', 'fnb')]"
    )


