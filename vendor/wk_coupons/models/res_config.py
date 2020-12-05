# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2017-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
# Developed By: Jahangir
#################################################################################
from odoo import api, fields, models, _
from datetime import datetime, timedelta
# from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class Company(models.Model):
    _inherit = 'res.company'

    wk_coupon_voucher_product_id = fields.Many2one('product.product')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    wk_coupon_name = fields.Char(string='Name', size=100 , help="default name of the coupon")

    @api.model
    def _get_default_voucher_product(self):
        return self.env.user.company_id.wk_coupon_voucher_product_id
        # ir_model_data = self.env['ir.model.data']
        # temp_id = ir_model_data.get_object_reference('wk_coupons', 'product_product_coupon')[1]
        # if temp_id:
        #     return temp_id

    wk_coupon_product_id = fields.Many2one(comodel_name='product.product', string='Coupon Product',
                                           default=_get_default_voucher_product)
    wk_coupon_min_amount = fields.Float(string='Minimum Voucher Value')
    wk_coupon_max_amount = fields.Float(string='Maximum Voucher Value')
    wk_coupon_max_expiry_date = fields.Date(string='Expiry Date',help="Date on which Voucher is expired.")
    wk_coupon_partially_use = fields.Boolean(string='Partially Use')
    wk_coupon_validity = fields.Integer(string='Validity(in days)', help="Validity of this Voucher in days")
    wk_coupon_availability = fields.Integer(string='Total Available', help="Total availability of this voucher")
    wk_coupon_value = fields.Float(string='Voucher Value')
    wk_coupon_voucher_usage = fields.Selection([('both', 'Both POS & Ecommerce'),('ecommerce', 'Ecommerce'),('pos', 'Point Of Sale')], string="Coupon Used In" ,help="Choose where you want to use the coupon pos/ecommerce and odoocore")
    wk_coupon_customer_type = fields.Selection([('special_customer', 'Special Customer'),('general', 'All Customers')], string="Customer Type" ,help="on choosing the General the coupon can be applied for all customers, and on choosing the Special Customer the Coupon can be used for a particlar customer and can be partially redeemed.")
    wk_coupon_partial_limit = fields.Integer('Partial Limit')
    wk_coupon_minumum_cart_value_usage = fields.Boolean('Use Cart Amount Validation', help="Use this option for using this voucher based on the cart amount.")
    wk_coupon_minimum_cart_amount = fields.Float('Minimum Cart Amount', help="Apply this coupon only if the cart value is greater than this amount.")

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        IrDefault = self.env['ir.default'].sudo()
        if self.wk_coupon_product_id:
            self.sudo().env.user.company_id.wk_coupon_voucher_product_id = self.wk_coupon_product_id

        # IrDefault.set('res.config.settings', 'wk_coupon_product_id',self.wk_coupon_product_id.id)

        IrDefault.set('res.config.settings', 'wk_coupon_min_amount',self.wk_coupon_min_amount)
        IrDefault.set('res.config.settings', 'wk_coupon_max_amount',self.wk_coupon_max_amount)
        IrDefault.set('res.config.settings', 'wk_coupon_max_expiry_date',self.wk_coupon_max_expiry_date)
        IrDefault.set('res.config.settings', 'wk_coupon_partially_use',self.wk_coupon_partially_use)
        IrDefault.set('res.config.settings', 'wk_coupon_validity',self.wk_coupon_validity)
        IrDefault.set('res.config.settings', 'wk_coupon_availability',self.wk_coupon_availability)
        IrDefault.set('res.config.settings', 'wk_coupon_value',self.wk_coupon_value)
        IrDefault.set('res.config.settings', 'wk_coupon_voucher_usage',self.wk_coupon_voucher_usage)
        IrDefault.set('res.config.settings', 'wk_coupon_customer_type',self.wk_coupon_customer_type)
        IrDefault.set('res.config.settings', 'wk_coupon_partial_limit',self.wk_coupon_partial_limit)
        IrDefault.set('res.config.settings', 'wk_coupon_minumum_cart_value_usage',self.wk_coupon_minumum_cart_value_usage)
        IrDefault.set('res.config.settings', 'wk_coupon_minimum_cart_amount',self.wk_coupon_minimum_cart_amount)
        IrDefault.set('res.config.settings', 'wk_coupon_name',self.wk_coupon_name)
        
        return True
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        default_voucher_product_per_company = self._get_default_voucher_product()
        IrDefault = self.env['ir.default'].sudo()
        res.update(
            {
            # 'wk_coupon_product_id':IrDefault.get('res.config.settings', 'wk_coupon_product_id') or self._get_default_voucher_product(),
                'wk_coupon_product_id': default_voucher_product_per_company.id if default_voucher_product_per_company
                    else False,

            'wk_coupon_min_amount':IrDefault.get('res.config.settings', 'wk_coupon_min_amount') or 0.0,
            'wk_coupon_max_amount':IrDefault.get('res.config.settings', 'wk_coupon_max_amount' ) or 9999,
            'wk_coupon_max_expiry_date':IrDefault.get('res.config.settings', 'wk_coupon_max_expiry_date' ) or datetime.now().date(),
            'wk_coupon_partially_use':IrDefault.get('res.config.settings', 'wk_coupon_partially_use' ) or False,
            'wk_coupon_validity':IrDefault.get('res.config.settings', 'wk_coupon_validity' ) or 0,
            'wk_coupon_availability':IrDefault.get('res.config.settings', 'wk_coupon_availability' ) or 10,
            'wk_coupon_value':IrDefault.get('res.config.settings', 'wk_coupon_value' ) or 100,
            'wk_coupon_voucher_usage':IrDefault.get('res.config.settings', 'wk_coupon_voucher_usage' ) or 'both',
            'wk_coupon_customer_type':IrDefault.get('res.config.settings', 'wk_coupon_customer_type' ) or 'general',
            'wk_coupon_partial_limit':IrDefault.get('res.config.settings', 'wk_coupon_partial_limit' ) or -1,
            'wk_coupon_minumum_cart_value_usage':IrDefault.get('res.config.settings', 'wk_coupon_minumum_cart_value_usage' )or True,
            'wk_coupon_minimum_cart_amount':IrDefault.get('res.config.settings', 'wk_coupon_minimum_cart_amount') or 1000,
            'wk_coupon_name':IrDefault.get('res.config.settings', 'wk_coupon_name') or "Default Coupon Name"
            
            }
        )
        return res
