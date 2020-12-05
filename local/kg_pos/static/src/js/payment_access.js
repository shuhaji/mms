odoo.define('kg_pos.payment_access', function(require) {
    'use strict'

    var models = require('point_of_sale.models')
    var screens = require('point_of_sale.screens')
    var gui = require('point_of_sale.gui')
    var popups = require('point_of_sale.popups')
    var core = require('web.core')
    var rpc = require('web.rpc')
    var chrome = require('point_of_sale.chrome')

    var _t = core._t
    var session = require('web.session')

    models.load_fields("res.users", "allow_payment_access");

    screens.PaymentScreenWidget.include({
        show: function(){
            var self = this
            this._super()
            if (this.pos.user.allow_payment_access) {
//                this._super()
            }
            else {
                if (this.pos.allowed_to_access_payment) {
//                    this._super()
                }
                else if (!this.pos.user.allowed_to_access_payment) {
//                    self.gui.show_screen('products');
                    $('body').off('keypress', self.keyboard_handler);
                    $('body').off('keydown', self.keyboard_keydown_handler);
                    this.gui.show_popup('security-pin', {
                        title: _t('Security PIN'),
                        confirm: function() {
                            var pin = this.$('#pin').val()
                            // note: manager PIN is from users that inside group of POS (both manager or user) and based on company
                            var user_by_pin = this.pos.users.find(user =>
                                user.pos_security_pin === pin && user.allow_payment_access)
                            if (user_by_pin) {
                                self.pos.allowed_to_access_payment = true;
                                // that one comes from BarcodeEvents
                                $('body').keypress(this.keyboard_handler);
                                // that one comes from the pos, but we prefer to cover all the basis
                                $('body').keydown(this.keyboard_keydown_handler);
                                self.gui.close_popup()
                            } else {
                                // back to screen products
                                self.gui.show_screen('products');
                                this.gui.show_popup('error', {
                                    title: _t('Invalid PIN'),
                                    body: _t(
                                        'No valid user found for this PIN'
                                    )
                                })
                            }
                            // this.gui.close_popup()
                        },
                        cancel: function () {
                            // back to screen products
                            self.gui.show_screen('products');
                            // this.gui.show_screen('receipt', null, refresh_screen);
                        },
                    })
                }
            }
        },
        click_back: function(){
            this.pos.allowed_to_access_payment = false
            this.pos.allowed_to_delete = false
            this._super()
            // this.gui.show_screen('products');
        },
        // validate_order: function(force_validation) {
        //     this.pos.allowed_to_access_payment = false
        //     this.pos.allowed_to_delete = false
        //     if (this.order_is_valid(force_validation)) {
        //         this.finalize_validation();
        //     }
        // },
    })

    chrome.OrderSelectorWidget.include({
        neworder_click_handler: function(event, $el) {
            this.pos.allowed_to_access_payment = false
            this.pos.allowed_to_delete = false
            this.pos.add_new_order();
        },
        order_click_handler: function(event,$el) {
            this.pos.allowed_to_access_payment = false
            this.pos.allowed_to_delete = false
            var order = this.get_order_by_uid($el.data('uid'));
            if (order) {
                this.pos.set_order(order);
            }
        },
    })
})
