# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, _


class KGPOSConfig(models.Model):
    _inherit = 'pos.config'

    discount_pc = fields.Float(string='Discount Percentage', help='The default discount percentage')

    my_value_outlet_id = fields.Char(
        'My Value Outlet_id',
    )

    meal_time_id = fields.Many2one(
        'meal.time',
        'Meal Time',
    )

    myvalue_minimum_redeem_point = fields.Float(
        'MyValue Minimum Redeem Point',
        default=0.0,
    )

    receipt_column_count = fields.Selection([
        ('1', 'Single'),
        ('2', 'Double (Left-Right)'),
    ], string='POS Receipt - Column Layout', default='1')

    receipt_bill_report_name = fields.Selection([
        ('single.mrt', '1. Single - Blank (single.mrt)'),
        ('double.mrt', '2. Double (Left-Right) - Blank (double.mrt)'),
        ('double-pre-printed.mrt', '3. Double - Pre-printed (double-pre-printed.mrt)'),
    ], string='POS Bill/Receipt', default='single.mrt')
    # Important: put mrt report files on : /kg_pos/static/rpt
    # receipt_bill_report_name = fields.Char(string='POS Bill/Receipt', default='single.mrt')
    #
    # @api.onchange('receipt_bill_report_selections')
    # def receipt_bill_report_selections_onchange(self):
    #     self.receipt_bill_report_name = self.receipt_bill_report_selections

    kitchen_order_report_name = fields.Selection([
        ('kitchen-order.mrt', '1. Standard Kitchen Order'),
    ], string='POS Kitchen Order', default=False
        , help='Select kitchen order report, select blank/empty value if not applicable (hide button)')

    @api.onchange('module_pos_restaurant')
    def _default_payment_access(self):
        if self.module_pos_restaurant is False:
            self.meal_time_id = False

    @api.multi
    def open_session_cb(self):
        """ new session button

        create one if none exist
        access cash control interface if enabled or start a session
        """
        self.ensure_one()
        if not self.current_session_id:
            self.current_session_id = self.env['pos.session'].create({
                'user_id': self.env.uid,
                'config_id': self.id
            })
            # always open session form, to edit shift and working date!
            # if self.current_session_id.state == 'opened':
            #    return self.open_ui()
            return self._open_session(self.current_session_id.id)
        return self._open_session(self.current_session_id.id)

