from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.model
    def _get_default_banquet_food_product_id(self):
        return self.env.user.company_id.banquet_food_product_id

    @api.model
    def _get_default_banquet_beverage_product_id(self):
        return self.env.user.company_id.banquet_beverage_product_id

    @api.model
    def _get_default_banquet_other_product_id(self):
        return self.env.user.company_id.banquet_other_product_id

    @api.model
    def _get_default_banquet_residential_product_id(self):
        return self.env.user.company_id.banquet_residential_product_id

    banquet_food_product_id = fields.Many2one('product.product', 'Food Product Id',
                                      default=_get_default_banquet_food_product_id)
    banquet_beverage_product_id = fields.Many2one('product.product', 'Beverage Product Id',
                                          default=_get_default_banquet_beverage_product_id)
    banquet_other_product_id = fields.Many2one('product.product', 'Other Product Id',
                                       default=_get_default_banquet_other_product_id)
    banquet_residential_product_id = fields.Many2one('product.product', 'Residential Product Id',
                                             default=_get_default_banquet_residential_product_id)

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        if self.banquet_food_product_id:
            self.sudo().env.user.company_id.banquet_food_product_id = self.banquet_food_product_id
        if self.banquet_beverage_product_id:
            self.sudo().env.user.company_id.banquet_beverage_product_id = self.banquet_beverage_product_id
        if self.banquet_other_product_id:
            self.sudo().env.user.company_id.banquet_other_product_id = self.banquet_other_product_id
        if self.banquet_residential_product_id:
            self.sudo().env.user.company_id.banquet_residential_product_id = self.banquet_residential_product_id
