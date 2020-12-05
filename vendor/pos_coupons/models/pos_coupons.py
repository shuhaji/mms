# -*- coding: utf-8 -*-
##########################################################################
#
#    Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
##########################################################################
from odoo import api, fields, models, _
from odoo import tools
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class res_users(models.Model):
    _inherit = 'res.users'

    allow_coupon_create = fields.Boolean('Allow Creation of Coupon(s)')


class VoucherVoucher(models.Model):
    _inherit = "voucher.voucher"

    @api.model
    def create_coupons(self, vals):
        vals['customer_type'] = vals['customer_type']
        vals['customer_id'] = vals.pop('partner_id')
        vals['name'] = vals['name']
        vals['validity'] = float(vals['validity'])
        vals['total_available'] = float(vals['total_available'])
        vals['voucher_value'] = float(vals.pop('coupon_value'))
        vals['note'] = vals['note']
        vals['issue_date'] = fields.Date.today()
        vals['voucher_code'] = False
        vals['redeemption_limit'] = vals['redeemption_limit']
        vals['is_partially_redemed'] = vals.pop('partial_redeem')
        vals['voucher_usage'] = vals['voucher_usage']
        vals['expiry_date'] =  vals['max_expiry_date']
        if vals['max_expiry_date'] < fields.Date.today():
            vals['expiry_date'] = fields.Date.today()
        if vals.get('amount_type'):
            vals['voucher_val_type'] = vals.pop('amount_type')
        vals.pop('max_expiry_date')
        return self.create(vals).id

    @api.model
    def get_coupon_data(self, coupon_id=False):
        if coupon_id:
            coupon = self.sudo().browse(coupon_id)
            return {
                'name': coupon.name,
                'coupon_code': coupon.voucher_code,
                'issue_date': coupon.issue_date,
                'expiry_date': coupon.issue_date,
                'coupon_value': coupon.voucher_value,
            }
        return False

    @api.model
    def wk_print_report(self):
        report_ids = self.env['ir.actions.report'].search(
            [('model', '=', 'voucher.voucher'), ('report_name', '=', 'wk_coupons.report_coupon')])
        return report_ids and report_ids[0].id

    @api.model
    def wk_get_default_product(self):
        return request.env['ir.default'].sudo().get('res.config.settings', 'wk_coupon_product_id')

    @api.model
    def return_voucher(self, coupon_id, line_id, refrence=False, history_id=False):
        voucher_obj = self.browse(coupon_id)
        if voucher_obj.customer_type == 'special_customer':
            if refrence == 'pos':
                if history_id:
                    history_obj = self.env[
                        'voucher.history'].browse(history_id)
                    if history_obj:
                        history_obj.unlink()
        return super(VoucherVoucher, self).return_voucher(coupon_id, line_id, refrence)

    @api.model
    def pos_create_histoy(self, coupon_id=False, wk_voucher_value=False, order_id=False, order_line_id=False, partner_id=False):
        values = {}
        if coupon_id:
            voucher_obj = self.browse(coupon_id)
            values = {
                'name': voucher_obj.name,
                'voucher_id': coupon_id,
                'voucher_value': -wk_voucher_value,
                'channel_used': 'pos',
                'transaction_type': 'debit',
                'pos_order_id': order_id,
                # 'pos_order_line_id':order_line_id,
                'user_id': partner_id,
            }
            self.env['voucher.history'].create(values)
            voucher_obj.sudo().write(
                {'total_available': voucher_obj.total_available - 1, 'date_of_last_usage': datetime.now().date()})
