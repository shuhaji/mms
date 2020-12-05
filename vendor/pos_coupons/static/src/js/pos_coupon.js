odoo.define('pos_coupon.pos_coupon', function(require) {
    "use strict";
    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var utils = require('web.utils');
    var rpc = require('web.rpc');
    var round_di = utils.round_decimals;
    var gui = require('point_of_sale.gui');
    var round_pr = utils.round_precision;
    var QWeb = core.qweb;
    var ActionManager = require('web.ActionManager');
    var PopupWidget = require("point_of_sale.popups");
    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var SuperPosModel = models.PosModel.prototype;
    var _t = core._t;
    models.load_fields('res.users', 'allow_coupon_create');
    
    // custom code by andi
    models.load_models({
        model: 'voucher.voucher',
        fields: [
            'name',
            'voucher_code',
            'voucher_usage',
            'customer_type',
            'active',
            'validity',
            'expiry_date',
            'issue_date',
            'applied_on',
            'voucher_value',
            'voucher_val_type',
            'total_available',
        ],
        loaded: function(self, voucher_coupons) {
            self.voucher_coupons = voucher_coupons
        },
    })

    var _super_order = models.Order.prototype
    models.Order = models.Order.extend({
        initialize: function() {
            _super_order.initialize.apply(this, arguments)
            this.coupon_id = this.coupon_id
            this.wk_product_id = this.wk_product_id
            this.wk_voucher_value = this.wk_voucher_value
            this.history_id = this.history_id
            this.save_to_db()
        },
        export_as_JSON: function() {
            var json = _super_order.export_as_JSON.apply(this, arguments)
            // json.meal_type = this.meal_type ? this.meal_type.name : undefined
            json.coupon_id = this.coupon_id
            json.wk_product_id = this.wk_product_id
            json.wk_voucher_value = this.wk_voucher_value
            json.history_id = this.history_id
            return json
        },
        init_from_JSON: function(json) {
            _super_order.init_from_JSON.apply(this, arguments)
            this.coupon_id = json.coupon_id
            this.wk_product_id = json.wk_product_id
            this.wk_voucher_value = json.wk_voucher_value
            this.history_id = json.history_id
        },
        export_for_printing: function() {
            var json = _super_order.export_for_printing.apply(this, arguments)
            json.coupon_id = this.coupon_id
            json.wk_product_id = this.wk_product_id
            json.wk_voucher_value = this.wk_voucher_value
            json.history_id = this.history_id
            
            return json
        },
        set_voucher_coupons: function(coupon_id, wk_product_id, wk_voucher_value, history_id) {
            this.coupon_id = coupon_id
            this.wk_product_id = wk_product_id
            this.wk_voucher_value = wk_voucher_value
            this.history_id = history_id

            this.trigger('change')
        },
        get_voucher_coupons: function () {
            var coupon_id = this.coupon_id
            var wk_product_id = this.wk_product_id
            var wk_voucher_value = this.wk_voucher_value
            var history_id = this.history_id

            return {
                coupon_id,
                wk_product_id,
                wk_voucher_value,
                history_id,
            }
        },
    });
    // end of custom code

    var CreateConfurmPopupWidget = PopupWidget.extend({
        template: 'CreateConfurmPopupWidget',

        show: function(wk_obj) {
            this._super();
            var self = this;
            var currentOrder = self.pos.get('selectedOrder');
            this.$('#print-coupons').off('click').click(function() {
                if (self.pos.config.iface_print_via_proxy) {
                        rpc.query({
                        model: 'voucher.voucher',
                        method: 'get_coupon_data',
                        args : [
                            wk_obj.wk_id],
                            })
                        .then(function(result){
                            var receipt = currentOrder.export_for_printing();
                            receipt['coupon'] = result;
                            var t = QWeb.render('CouponXmlReceipt', {
                                receipt: receipt,
                                widget: self,
                            });
                            self.pos.proxy.print_receipt(t);
                        });

                } else {
                    console.log("Created Cpn");
                    console.log(wk_obj.wk_id);
                    self.pos.chrome.do_action('wk_coupons.coupons_report',{
                        additional_context:{
                            active_ids: [wk_obj.wk_id],
                        }
                    });
                    self.gui.show_screen('products');
                }
            });
        },
    });
    gui.define_popup({
        name: 'create-confurm-screen',
        widget: CreateConfurmPopupWidget
    });

    var CreateCouponPopupWidget = PopupWidget.extend({
        template: 'CreateCouponPopupWidget',
        
        saveBackend: function(name, validity, availability, coupon_value, note, customer_type, partner_id, voucher_usage, amount_type, max_expiry_date, redeemption_limit, partial_redeem) {
            self = this;
            rpc.query({
                model: 'voucher.voucher',
                method: 'create_coupons',
                args: [{
                    'name': name,
                    'validity': validity,
                    'total_available': availability,
                    'coupon_value': coupon_value,
                    'note': note,
                    'customer_type': customer_type,
                    'partner_id': partner_id,
                    'voucher_usage': voucher_usage,
                    'amount_type': amount_type,
                    'max_expiry_date': max_expiry_date,
                    'redeemption_limit': redeemption_limit,
                    'partial_redeem': partial_redeem
                }],
            })
            .done(function(result){
                self.gui.show_popup('create-confurm-screen', {
                        'wk_id': result,
                });
            });
        },

        renderElement: function() {
            var self = this;
            this._super();
            var wk_coupon_product_id = null;
            rpc.query({
                model: 'voucher.voucher',
                method: 'get_default_values',
            })
            .done(function(result){
                self.wk_coupon_product_id = result.product_id;
                self.max_expiry_date = result.max_expiry_date;
                self.min_amount = result.min_amount;
                self.max_amount = result.max_amount;
                if(result.product_id != null)
                {
                    $("input[name=wk_coupon_validity]").val(result.default_validity);
                    $("input[name=wk_coupon_availability]").val(result.default_availability);
                    $("input[name=wk_coupon_value]").val(result.default_value);
                    $("select[name=wk_customer_type]").val(result.customer_type);
                    $("input[name=wk_redeemption_limit]").val(result.partial_limit);
                    $("input[name=wk_coupon_name]").val(result.wk_coupon_name);
                    $("#wk_partial_redeemed").attr('checked', result.partially_use);
                }
            });
            $("select[name=wk_customer_type]").change(function() {
                if ($(this).val() == 'special_customer') {
                    $("input[name=wk_coupon_availability]").parent().hide();
                    $("#wk_partial_redeemed").parent().parent().parent().show();
                } else {
                    $("input[name=wk_coupon_availability]").parent().show();
                    $("#wk_partial_redeemed").parent().parent().parent().hide();
                }
            });
            this.$('.wk_create_coupon_button').click(function() {
                function isNumber(o) {
                    return !isNaN(o - 0) && o !== null && o !== "" && o !== false;
                }
                var order = self.pos.get('selectedOrder');
                if (self.wk_coupon_product_id == null) {
                    self.gui.show_popup('error', {
                        'title': _t('Error !!!'),
                        'body': _t("Coupon Configuration is Required"),
                    });
                } else {
                    $("select[name=wk_partner_id]").removeClass("wk_text_error");
                    $('.wk_valid_error').html("");
                    var name = $("input[name=wk_coupon_name]").removeClass("wk_text_error").val();
                    var validity = $("input[name=wk_coupon_validity]").removeClass("wk_text_error").val();
                    var availability = $("input[name=wk_coupon_availability]").removeClass("wk_text_error").val();
                    var coupon_value = $("input[name=wk_coupon_value]").removeClass("wk_text_error").val();
                    var note = $("textarea[name=note]").val();
                    var customer_type = $("select[name=wk_customer_type]").removeClass("wk_text_error").val();
                    var voucher_usage = $("select[name=wk_coupon_usage]").removeClass("wk_text_error").val();
                    var redeemption_limit = $("input[name=wk_redeemption_limit]").removeClass("wk_text_error").val();
                    var partial_redeem = $("#wk_partial_redeemed").is(":checked");
                    var amount_type = $("select[name=wk_amount_type]").removeClass("wk_text_error").val();
                    var max_expiry_date = self.max_expiry_date;
                    var min_amount = self.min_amount;
                    var max_amount = self.max_amount;
                    if (name != '') {
                        if (isNumber(validity)) {
                            if (isNumber(availability) && availability != 0) {
                                if (isNumber(coupon_value) && coupon_value != 0) {
                                    if (!(amount_type == 'percent' && (coupon_value < 0 || coupon_value > 100))) {
                                        if (parseInt(coupon_value) >= min_amount && parseInt(coupon_value) <= max_amount) {
                                            if (customer_type == 'special_customer') {
                                                if (order.get_client() == null) {
                                                    self.gui.show_popup('error', {
                                                        'title': _t('Error !!!'),
                                                        'body': _t("Please Select Customer!!!!"),
                                                    });
                                                } else {
                                                    if (partial_redeem == true) {
                                                        if (redeemption_limit == 0)
                                                            $('.valid_error_redeeemption').html("This field is required & should not be 0");
                                                        else {
                                                            self.saveBackend(name, validity, availability, coupon_value, note, customer_type, order.get_client().id, voucher_usage, amount_type, max_expiry_date, redeemption_limit, partial_redeem);
                                                        }

                                                    } else
                                                        self.saveBackend(name, validity, availability, coupon_value, note, customer_type, order.get_client().id, voucher_usage, amount_type, max_expiry_date, -1, false);
                                                }
                                            } else
                                                self.saveBackend(name, validity, availability, coupon_value, note, customer_type, false, voucher_usage, amount_type, max_expiry_date, -1, false);
                                        } else {
                                            if (parseInt(coupon_value) < min_amount)
                                                $("input[name=wk_coupon_value]").parent().find('.wk_valid_error').html("(Min. allowed value is " + min_amount + ")");
                                            else
                                                $("input[name=wk_coupon_value]").parent().find('.wk_valid_error').html("(Max. allowed value is " + max_amount + ")");
                                        }
                                    } else {
                                        $("input[name=wk_coupon_value]").parent().find('.wk_valid_error').html("Must be > 0 & <=100");
                                    }
                                } else {
                                    $("input[name=wk_coupon_value]").addClass("wk_text_error");
                                    $("input[name=wk_coupon_value]").parent().find('.wk_valid_error').html("Value should be >=0");
                                }
                            } else {
                                $("input[name=wk_coupon_availability]").addClass("wk_text_error");
                                $("input[name=wk_coupon_availability]").parent().find('.wk_valid_error').html("Validity can't be 0");
                            }
                        } else
                            $("input[name=wk_coupon_validity]").addClass("wk_text_error");
                    } else
                        $("input[name=wk_coupon_name]").addClass("wk_text_error");
                }
            });
        },
    });
    gui.define_popup({
        name: 'create_coupon_popup_widget',
        widget: CreateCouponPopupWidget
    });

    var RedeemPopupRetryWidget = PopupWidget.extend({
        template: 'RedeemPopupRetryWidget',
        show: function(options) {
            this._super(options);
            this.gui.play_sound('error');
        },
        renderElement: function() {
            var self = this;
            this._super();
            this.$('#wk-retry-coupons').click(function() {
                self.gui.show_popup('redeem_coupon_popup_widget', {});
            });
        },
    });
    gui.define_popup({
        name: 'redeem_coupon_retry_popup_widget',
        widget: RedeemPopupRetryWidget
    });

    var RedeemPopupValidateWidget = PopupWidget.extend({
        template: 'RedeemPopupValidateWidget',

        show: function(options) {
            var self = this;
            this._super(options);
            self.wk_product_id = options.wk_product_id;
            self.secret_code = options.secret_code;
            self.total_val = options.total_val;
            self.coupon_name = options.coupon_name;
        },
        renderElement: function() {
            var self = this;
            this._super();
            var selectedOrder = self.pos.get('selectedOrder');

            this.$('#wk-retry-coupons').click(function() {
                rpc.query({
                        model: 'voucher.voucher',
                        method: 'redeem_voucher_create_histoy',
                        args : [self.coupon_name, self.secret_code, self.total_val, false, false, 'pos'],
                        }).done(function(result) {
                            if (result['status']) {

                                selectedOrder.coupon_id = self.secret_code;
                                selectedOrder.wk_product_id = self.wk_product_id;
                                selectedOrder.wk_voucher_value = self.total_val;
                                selectedOrder.history_id = result['history_id'];

                                // custom code by andi
                                selectedOrder.set_voucher_coupons(
                                        selectedOrder.coupon_id, 
                                        selectedOrder.wk_product_id,
                                        selectedOrder.wk_voucher_value,
                                        selectedOrder.history_id,
                                    )
                                // end of custom code

                                var product = self.pos.db.get_product_by_id(self.wk_product_id);
                                var last_orderline = selectedOrder.get_last_orderline();
                                last_orderline.coupon_name = self.coupon_name;
                                if (product != undefined) {
                                    selectedOrder.add_product(product, {
                                        price: -(self.total_val)
                                    });
                                    self.gui.show_screen('products');
                                } else {
                                    self.gui.show_popup('error', {
                                        'title': _t('Error !!!'),
                                        'body': _t("Voucher product not available in POS. Please make the voucher product available in POS"),
                                    });
                                }
                            }
                        }).fail(function(unused, event) {
                            self.gui.show_popup('error', {
                                'title': _t('Error !!!'),
                                'body': _t("Connection Error. Try again later !!!!"),
                        });
                    });
            });
        },
    });
    gui.define_popup({
        name: 'redeem_coupon_validate_popup_widget',
        widget: RedeemPopupValidateWidget
    });

    var RedeemPopupWidget = PopupWidget.extend({
        template: 'RedeemPopupWidget',

        renderElement: function() {
            var self = this;
            this._super();
            var order = self.pos.get('selectedOrder');
            if (order == null) {
                return false;
            }
            var orderlines = order.orderlines;
            var coupon_product = true;
            var prod_list = []
            var selected_prod_percent_price = 0
            for (var i = 0; i < orderlines.models.length; i++) {
                prod_list.push(orderlines.models[i].product.id);
            }
            this.$('#wk-redeem-coupons').click(function() {
                var secret_code = $("#coupon_8d_code").val();
                rpc.query({
                        model: 'voucher.voucher',
                        method: 'validate_voucher',
                        args :[secret_code, order.get_total_without_tax(), prod_list, 'pos', order.get_client() ? order.get_client().id : 0]
                        }).fail(function(unused, event) {
                            self.gui.show_popup('error', {
                                'title': _t('Error !!!'),
                                'body': _t('Connection Error. Try again later !!!!'),
                            });
                    }).done(function(result) {
                        if (orderlines.models.length) {
                            for (var i = 0; i < orderlines.models.length; i++) {
                                if (orderlines.models[i].product.id == result.product_id)
                                    coupon_product = false;
                                if (result.product_ids !== undefined)
                                    if ($.inArray(orderlines.models[i].product.product_tmpl_id, result.product_ids) !== -1)
                                        selected_prod_percent_price += orderlines.models[i].price * orderlines.models[i].quantity;
                            }
                            if (coupon_product) {
                                if (result.status) {
                                    // original code
                                    // var total_amount = order.get_total_with_tax();
                                    // end of original code

                                    // custom code by andi
                                    var total_amount = order.get_total_without_tax() || 0.0;
                                    // end of custom code by andi
                                    
                                    var msg;
                                    var total_val;
                                    var res_value = result.value;
                                    if (result.customer_type == 'general') {
                                        if (result.voucher_val_type == 'percent') {
                                            res_value = (total_amount * result.value) / 100;
                                            if (result.applied_on == 'specific')
                                                res_value = (selected_prod_percent_price * result.value) / 100;
                                            else
                                                total_amount = res_value;
                                        } else {
                                            if (result.applied_on == 'specific')
                                                total_amount = selected_prod_percent_price
                                        }
                                    }
                                    if (total_amount < res_value) {
                                        msg = total_amount;
                                        total_val = total_amount;
                                    } else {
                                        msg = res_value;
                                        total_val = res_value;
                                    }
                                    msg = parseFloat(round_di(msg, 2).toFixed(2));
                                    self.gui.show_popup('redeem_coupon_validate_popup_widget', {
                                        'title': _t(result.message),
                                        'msg': _t(msg),
                                        'wk_product_id': result.product_id,
                                        'secret_code': result.coupon_id,
                                        'total_val': total_val,
                                        'coupon_name': result.coupon_name,
                                        'coupon_code': result.voucher_code,

                                    });
                                } else {
                                    self.gui.show_popup('redeem_coupon_retry_popup_widget', {
                                        'title': _t("Error: " + result.message),
                                    });
                                }
                            } else {
                                self.gui.show_popup('error', {
                                    'title': _t('Error !!!'),
                                    'body': _t("Sorry, you can't use more than one coupon in single order."),
                                });
                            }
                        } else {
                            self.gui.show_popup('error', {
                                'title': _t('Error !!!'),
                                'body': _t("Sorry, there is no product in order line."),
                            });
                        }
                    });
            });
        },
    });
    gui.define_popup({
        name: 'redeem_coupon_popup_widget',
        widget: RedeemPopupWidget
    });

    var VoucherCouponPopupWidget = PopupWidget.extend({
        template: 'VoucherCouponPopupWidget',

        renderElement: function() {
            var self = this;
            this._super();
            this.$('#gift-coupons-create').click(function() {
                if (self.pos.user.allow_coupon_create)
                    self.gui.show_popup('create_coupon_popup_widget', {});
                else {
                    self.gui.show_popup('error', {
                        'title': _t('Error !!!'),
                        'body': _t("Access denied please contact your Administrator"),
                    });
                }
            });
            this.$('#gift-coupons-redeem').click(function() {
                self.gui.show_popup('redeem_coupon_popup_widget', {});
                $('#coupon_8d_code').focus();
            });
        },
    });
    gui.define_popup({
        name: 'coupon_popup_widget',
        widget: VoucherCouponPopupWidget
    });

    var CouponButtonWidget = screens.ActionButtonWidget.extend({
        template: 'CouponButtonWidget',
        button_click: function() {
            self = this;
            self.gui.show_popup('coupon_popup_widget', {});
        },
    });
    screens.define_action_button({
        'name': 'Coupon',
        'widget': CouponButtonWidget,
        'condition': function() {
            return true;
        },
    });

    var _super = models.Order;
    models.Order = models.Order.extend({
        initialize: function(attributes) {
            this.coupon_id = 0;
            this.wk_product_id = 0;
            this.history_id = 0;
            _super.prototype.initialize.apply(this, arguments);
        },
        export_as_JSON: function() {
            var json = _super.prototype.export_as_JSON.apply(this, arguments);
            var order = this.pos.get('selectedOrder');
            if (order != null) {
                var orderlines = order.orderlines;
                var coupon_state = true;
                for (var i = 0; i < orderlines.models.length; i++)
                    if (orderlines.models[i].product.id == order.wk_product_id)
                        coupon_state = false;
                if (coupon_state)
                    json.coupon_id = 0;
                else
                    json.coupon_id = order.coupon_id || 0;
            }
            return json;
        },
    });

    models.PosModel = models.PosModel.extend({
        _save_to_server: function(orders, options) {
            var self = this;
            var wk_order = self.get_order();
            return SuperPosModel._save_to_server.call(this, orders, options).then(function(server_ids) {
                /*-------------CODE FOR POS VOUCHERS START------*/
                if (server_ids) {
                    if (wk_order != null) {
                        var coupon_id = wk_order.coupon_id;
                        var wk_product_id = wk_order.wk_product_id;
                        var wk_voucher_value = wk_order.wk_voucher_value;
                        for (var i = 0; i < wk_order.orderlines.models.length; i++) {
                            $('.receipt-screen.screen span.button.next').show();
                            if (wk_order.orderlines.models[i].product.id == wk_product_id) {
                                var client_id = false;
                                if (self.get_client()) {
                                    client_id = self.get_client().id;
                                }
                                console.log('wk_orderlines', wk_order.orderlines.models[i].id);
                                rpc.query({
                                    model: 'voucher.voucher',
                                    method: 'pos_create_histoy',
                                    args :  [coupon_id, wk_voucher_value, server_ids[0], wk_order.orderlines.models[i].id, client_id],
                                    }).fail(function(unused, event) {
                                        self.gui.show_popup('error', {
                                            'title': _t('Error !!!'),
                                            'body': _t("Connection Error. Try again later !!!"),
                                        });
                                    })
                                    .done(function(result) {
                                        console.log('-------------------%r',result);
                                    });
                            }
                        }
                    }
                }
                /*-------------CODE FOR POS VOUCHERS END------*/
                return server_ids;
            });
        },
    });


    screens.NumpadWidget.include({
        clickAppendNewChar: function(event) {
            var order = this.pos.get_order();
            var p_id = order.get_selected_orderline();
            if (order.get_selected_orderline() && (order.wk_product_id === order.get_selected_orderline().product.id)) {
                self.gui.show_popup('error', {
                    'title': _t('Error !!!'),
                    'body': _t("You can not change the quantity, discount or price of the applied voucher"),
                });
            } else {
                this._super(event);
            }
        },
    });
 screens.ReceiptScreenWidget.include({
        click_next: function() {
        $('.receipt-screen.screen span.button.next').hide();
        this.pos.get_order().finalize();
    },
    });

});