# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "Pos Coupons And Vouchers",
  "summary"              :  "Add an option in existing Point Of Sale to Create and Use Coupons/Vouchers on Current Order.",
  "category"             :  "Point of sale",
  "version"              :  "3.0.2",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/OpenERP-POS-Coupons.html",
  "description"          :  "http://webkul.com/blog/odoo-pos-vouchers/",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=pos_coupons&version=11.0",
  "depends"              :  [
                             'point_of_sale',
                             'wk_coupons',
                            ],
  "data"                 :  [
                             'views/inherited_voucher_history_view.xml',
                             'views/pos_coupons_view.xml',
                             'views/templates.xml',
                            ],
  "qweb"                 :  ['static/src/xml/*.xml'],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  124,
  "currency"             :  "EUR",
  "pre_init_hook"        :  "pre_init_check",
}