odoo.define('kg_pos.payment_method', function(require) {
    'use_strict'

    var models = require('point_of_sale.models')
    var screens = require('point_of_sale.screens')
    var gui = require('point_of_sale.gui')
    var popups = require('point_of_sale.popups')
    var core = require('web.core')
    var field_utils = require('web.field_utils')
    var utils = require('web.utils');
    var BarcodeEvents = require('barcodes.BarcodeEvents').BarcodeEvents;
    var rpc = require('web.rpc')
    var round_di = utils.round_decimals;
    // var numeral = require('numeral');

    var _t = core._t
    var round_pr = utils.round_precision;
    var QWeb = core.qweb;

    models.load_models({
        model: 'account.journal',
        fields: [
            'name',
            'type',
            'sequence',
            'is_department_expense',
            'is_officer_check',
            'is_city_ledger',
            'is_advance_payment',
            'is_issuer_bank',
            'is_charge_room',
            'is_point',
            'split_payment',
            'is_voucher',
        ],
        domain: function(self, tmp) {
            return [['id', 'in', tmp.journals]]
        },
        loaded: function(self, journals) {
            var i
            self.journals = journals

            // associate the bank statements with their journals.
            var cashregisters = self.cashregisters
            var ilen = cashregisters.length
            for (i = 0; i < ilen; i++) {
                for (var j = 0, jlen = journals.length; j < jlen; j++) {
                    if (cashregisters[i].journal_id[0] === journals[j].id) {
                        cashregisters[i].journal = journals[j]
                    }
                }
            }

            self.cashregisters_by_id = {}
            for (i = 0; i < self.cashregisters.length; i++) {
                self.cashregisters_by_id[self.cashregisters[i].id] =
                    self.cashregisters[i]
            }

            self.cashregisters = self.cashregisters.sort(function(a, b) {
                // prefer cashregisters to be first in the list
                if (a.journal.type == 'cash' && b.journal.type != 'cash') {
                    return -1
                } else if (
                    a.journal.type != 'cash' &&
                    b.journal.type == 'cash'
                ) {
                    return 1
                } else {
                    return a.journal.sequence - b.journal.sequence
                }
            })

            // self.issuer_banks = []
            // for (var i = 0; i < self.cashregisters.length; i++) {
            //     if (
            //         self.cashregisters[i].journal.type === 'bank' &&
            //         self.cashregisters[i].journal.is_issuer_bank
            //     ) {
            //         self.issuer_banks.push(self.cashregisters[i].journal)
            //     }
            // }
        },
    })

    models.load_models({
        model: 'kg.issuer.type',
        fields: ['name'],
        domain: [['name', '!=', false]],
        loaded: function(self, issuer_types) {
            self.issuer_types = issuer_types

            // self.selected_issuer_types = issuer_types
//            for (var h = 0; h < self.issuer_banks.length; h++) {
//                if (self.issuer_banks[h].issuer_type_ids[0]) {
//                    for (var i = 0; i < self.issuer_types.length; i++) {
//                        for (
//                            var j = 0;
//                            j < self.issuer_banks[h].issuer_type_ids.length;
//                            j++
//                        ) {
//                            if (
//                                self.issuer_banks[h].issuer_type_ids[j] ===
//                                self.issuer_types[i].id
//                            ) {
//                                self.selected_issuer_types.push(
//                                    self.issuer_types[i]
//                                )
//                            }
//                        }
//                    }
//                }
//            }
        },
    });

    // load custom fields on service tax account to pos offline db
    models.load_fields("account.tax", "is_service_charge");

    var _super_order = models.Order.prototype
    models.Order = models.Order.extend({
        initialize: function(attr,options) {
            _super_order.initialize.apply(this, arguments)
            this.full_used_adv_payment = options.full_used_adv_payment
            this.used_adv_payment = options.used_adv_payment
            this.list_of_adv_payments = options.list_of_adv_payments
            this.list_of_taxes = options.list_of_taxes
            this.allow_to_validate_payment = options.allow_to_validate_payment
            this.my_value_redeem_response = options.my_value_redeem_response
            this.my_value_redeem_response_code = options.my_value_redeem_response_code
            this.my_value_earn_response = options.my_value_earn_response
            this.my_value_earn_response_code = options.my_value_earn_response_code
            this.redeem_transaction_check = options.redeem_transaction_check
            this.allow_press_payment_numpad = options.allow_press_payment_numpad
            this.discount_amount_total = options.discount_amount_total || 0
            this.discount_pct_global = options.discount_pct_global || 0
            this.discount_type = options.discount_type || "pct" // amount vs pct vs null/nothing
            this.outlet_id = options.outlet_id || false;
            this.save_to_db()
            return this;
        },
        export_as_JSON: function() {
            var json = _super_order.export_as_JSON.apply(this, arguments)
            // json.meal_type = this.meal_type ? this.meal_type.name : undefined
            json.full_used_adv_payment = this.full_used_adv_payment
            json.used_adv_payment = this.used_adv_payment
            json.list_of_adv_payments = this.list_of_adv_payments
            json.list_of_taxes = this.list_of_taxes
            json.allow_to_validate_payment = this.allow_to_validate_payment
            json.my_value_redeem_response = this.my_value_redeem_response
            json.my_value_redeem_response_code = this.my_value_redeem_response_code
            json.my_value_earn_response = this.my_value_earn_response
            json.my_value_earn_response_code = this.my_value_earn_response_code
            json.redeem_transaction_check = this.redeem_transaction_check
            json.allow_press_payment_numpad = this.allow_press_payment_numpad
            json.discount_amount_total = this.discount_amount_total
            json.discount_pct_global = this.discount_pct_global
            json.discount_type = this.discount_type
            json.outlet_id = this.outlet_id
            return json
        },
        init_from_JSON: function(json) {
            _super_order.init_from_JSON.apply(this, arguments)
            this.full_used_adv_payment = json.full_used_adv_payment
            this.used_adv_payment = json.used_adv_payment
            this.list_of_adv_payments = json.list_of_adv_payments
            this.list_of_taxes = json.list_of_taxes
            this.allow_to_validate_payment = json.allow_to_validate_payment
            this.my_value_redeem_response = json.my_value_redeem_response
            this.my_value_redeem_response_code = json.my_value_redeem_response_code
            this.my_value_earn_response = json.my_value_earn_response
            this.my_value_earn_response_code = json.my_value_earn_response_code
            this.redeem_transaction_check = json.redeem_transaction_check
            this.allow_press_payment_numpad = json.allow_press_payment_numpad
            this.discount_amount_total = json.discount_amount_total
            this.discount_pct_global = json.discount_pct_global
            this.discount_type = json.discount_type
            this.outlet_id = json.outlet_id
        },
        export_for_printing: function() {
            var json = _super_order.export_for_printing.apply(this, arguments)
            json.full_used_adv_payment = this.full_used_adv_payment
            json.used_adv_payment = this.used_adv_payment
            json.list_of_adv_payments = this.list_of_adv_payments
            json.list_of_taxes = this.list_of_taxes
            json.allow_to_validate_payment = this.allow_to_validate_payment
            json.my_value_redeem_response = this.my_value_redeem_response
            json.my_value_redeem_response_code = this.my_value_redeem_response_code
            json.my_value_earn_response = this.my_value_earn_response
            json.my_value_earn_response_code = this.my_value_earn_response_code
            json.redeem_transaction_check = this.redeem_transaction_check
            json.allow_press_payment_numpad = this.allow_press_payment_numpad
            json.discount_amount_total = this.discount_amount_total
            json.discount_pct_global = this.discount_pct_global
            json.discount_type = this.discount_type
            json.outlet_id = this.outlet_id
            return json
        },
        get_due: function(paymentline) {
            var orderTotal;
            if (!!this.department_id || !!this.employee_id) {
                // is_department_expense or is_office_check
                orderTotal = this.get_total_without_tax()
            } else {
                orderTotal = this.get_total_with_tax()
            }

            if (!paymentline) {
                // var due = this.get_total_with_tax() - this.get_total_paid();
                var due = orderTotal - this.get_total_paid();
            } else {
                // var due = this.get_total_with_tax();
                var due = orderTotal;
                var lines = this.paymentlines.models;
                for (var i = 0; i < lines.length; i++) {
                    if (lines[i] === paymentline) {
                        break;
                    } else {
                        due -= lines[i].get_amount();
                    }
                }
            }
            return round_pr(due, this.pos.currency.rounding);
        },
        add_paymentline: function(cashregister) {
            this.assert_editable()
            var newPaymentline = new models.Paymentline(
                {},
                { order: this, cashregister: cashregister, pos: this.pos }
            )

            if (!this.selected_cashregister) {
                this.pos.gui.show_popup('error', {
                    title: _t('Payment Method'),
                    body: _t(
                        'Please select payment method'
                    ),
                })
            }
            else {
                if (this.get_due() === 0 &&
                        (!cashregister.journal.is_officer_check && !cashregister.journal.is_department_expense)) {
                    this.pos.gui.show_popup('error', {
                        title: _t('Full Payment'),
                        body: _t(
                            'The payment has been paid off'
                        ),
                    })
                }

                if (
                    cashregister.journal.type !== 'cash' ||
                    this.pos.config.iface_precompute_cash
                ) {
                    newPaymentline.set_amount(this.get_due())
                }

                if (cashregister.journal.is_officer_check) {
                    newPaymentline.set_amount(this.get_due())
                }

                else if (cashregister.journal.is_department_expense) {
                    newPaymentline.set_amount(this.get_due())
                }

                else if (cashregister.journal.is_city_ledger) {
                    newPaymentline.set_amount(this.get_due())
                }

                else if (cashregister.journal.is_advance_payment) {
                    newPaymentline.adv_payment = []
                    // add advance payment id
                    newPaymentline.adv_payment.push(this.adv_payment)
                    newPaymentline.set_amount(this.adv_payment_new_payment_amount)
                }

                else if (cashregister.journal.is_point) {
                    var my_value_points_used = this.pos.get_order().my_value_points_used || 0.0
                    newPaymentline.set_amount(my_value_points_used)
                }

                this.paymentlines.add(newPaymentline)
                this.select_paymentline(newPaymentline)
            }
        },
        get_new_total: function() {
            return this.get_total_with_tax()
        },
        set_list_adv_payment: function (adv_payment_list) {
            this.list_of_adv_payments = adv_payment_list

            this.trigger('change')
        },
        get_all_order_totals: function() {
            var total_service = 0;
            var total_tax_without_service = 0;
            var total_brutto = 0;
            var total_disc_amount_before_tax = 0;
            var total_netto_before_tax = 0
            var total_with_tax = 0
            var order = this
            if (order) {
                if (order.orderlines){
                    order.orderlines.forEach(function(line) {
                        all_prices = line.get_all_prices()
                        total_service += all_prices.serviceAmount
                        total_tax_without_service += all_prices.taxWithoutService
                        total_brutto += all_prices.bruttoBeforeTax
                        total_disc_amount_before_tax += all_prices.lineDiscAmountBeforeTax
                        total_netto_before_tax += all_prices.priceWithoutTax
                        total_with_tax += all_prices.priceWithTax
                    })
                }
            }
            return {
                 // Sub Total before discount and before tax/service
                totalBruttoBeforeTax: total_brutto,
                 // Amount discount before tax/service
                totalDiscAmountBeforeTax: total_disc_amount_before_tax,
                // discount amount (tax/services included)
                // totalDiscAmountWithTax: order.get_total_discount(),
                // sub Total after discount, before tax/service calculation (without tax/service)
                totalBeforeTax: total_netto_before_tax,
                // sub total after discount and tax/service:
                totalWithTax: total_with_tax,
                totalServiceAmount: total_service,
                totalTaxWithoutService: total_tax_without_service,
            };
        },
        get_total_tax: function() {
            if (!!this.department_id || !!this.employee_id) {
                // is_officer_check or is_department_expense
                return 0
            } else {
                return _super_order.get_total_tax.apply(this, arguments)
            }
        },
        get_list_of_taxes: function() {
            var order = this

            var taxes_by_id = []
            var list_of_taxes = []
            var order_lines = []
            var current_voucher = false
            var voucher_order_line = false

            var zero_tax_service = (!!order.department_id || !!order.employee_id) ? true : false

            if (order && !zero_tax_service) {

                // check if voucher coupon has been deleted from screen
                if (order.orderlines){
                    if (order.orderlines.models.length > 0) {
                        product_id_in_orderlines  = order.orderlines.models.map(line => line.product.id)
                        voucher_order_line = order.orderlines.models.filter(line => line.product.id === order.wk_product_id)[0]
                        if (voucher_order_line) {
                            if (voucher_order_line.get_base_price() === 0.0) {
                                order.coupon_id = 0.0
                            }
                        }
                    }
                }

                // set current voucher
                if (order.get_voucher_coupons().coupon_id || order.coupon_id) {
                    if (this.pos.voucher_coupons) {
                        if (this.pos.voucher_coupons.length > 0) {
                            for (var z = 0; z < this.pos.voucher_coupons.length; z++) {
                                var current_voucher = this.pos.voucher_coupons[z] || false
                                if (this.pos.voucher_coupons[z].id === order.coupon_id) {
                                    current_voucher = this.pos.voucher_coupons[z]
                                    break;
                                }
                            }
                        }
                    }
                }

                if (order.orderlines) {
                    lines = order.orderlines
                    if (lines.models.length > 0) {
                        for (var i = 0; i < lines.models.length; i++) {
                            order_line = lines.models[i]

                            //var price_unit = order_line.get_display_price() || 0.0
                            var price_unit = order_line.get_base_price() || 0.0
                            // var quantity = order_line.quantity
                            var quantity = 1
                            var currency_rounding = this.pos.currency.rounding

                            var list_taxes = [];
                            var currency_rounding_bak = currency_rounding;
                            if (this.pos.company.tax_calculation_rounding_method == "round_globally"){
                                currency_rounding = currency_rounding * 0.00001;
                            }
                            var total_excluded = round_pr(price_unit * quantity, currency_rounding);
                            var total_included = total_excluded;
                            var base = total_excluded;
                            var tax_amount = 0.0

                            if (order_line.product.taxes_id.length > 0) {
                                for (var j = 0; j < order_line.product.taxes_id.length; j++) {
                                    tax_id = order_line.product.taxes_id[j]
                                    current_tax = this.pos.taxes.filter(tax => tax.id === tax_id)[0]

                                    if (!current_tax){
                                        return;
                                    }

                                    if (current_tax.amount_type === 'group'){

                                        // applied voucher coupons
                                        if (current_voucher) {
                                            if (order_line.product.id !== order.wk_product_id) {
                                                var amount_voucher = 0.0
                                                if (current_voucher.voucher_val_type === 'percent') {
                                                    amount_voucher = (order.get_total_without_tax() + order.wk_voucher_value) * current_voucher.voucher_value / 100

                                                    if (current_voucher && j === 0) {
                                                        base = base - (base * current_voucher.voucher_value / 100)
                                                    }
                                                }

                                                else if (current_voucher.voucher_val_type === 'amount') {
                                                    amount_voucher = current_voucher.voucher_value
                                                    total_order_without_voucher = order.get_total_without_tax() + order.wk_voucher_value
                                                    total_voucher_per_order_line = (price_unit / total_order_without_voucher) * amount_voucher
                                                    total_voucher_per_order_line = round_pr(total_voucher_per_order_line, currency_rounding)
                                                    base = price_unit - total_voucher_per_order_line

                                                    if (current_voucher && j !== 0) {
                                                        base += tax_amount
                                                        base = round_pr(base, currency_rounding)
                                                    }
                                                }
                                            }
                                        }

                                        var ret = order_line.compute_all(current_tax.children_tax_ids, price_unit, quantity, currency_rounding);
                                        total_excluded = ret.total_excluded;
                                        base = ret.total_excluded;
                                        tax_amount = ret.total_included;
                                        tax_amount = round_pr(tax_amount, currency_rounding);
                                    }
                                    else if (current_tax.amount_type !== 'group') {

                                        // applied voucher coupons
                                        if (current_voucher) {
                                            if (order_line.product.id !== order.wk_product_id) {
                                                var amount_voucher = 0.0
                                                if (current_voucher.voucher_val_type === 'percent') {
                                                    amount_voucher = (order.get_total_without_tax() + order.wk_voucher_value) * current_voucher.voucher_value / 100

                                                    if (current_voucher && j === 0) {
                                                        base = base - (base * current_voucher.voucher_value / 100)
                                                    }
                                                }

                                                else if (current_voucher.voucher_val_type === 'amount') {
                                                    amount_voucher = current_voucher.voucher_value
                                                    total_order_without_voucher = order.get_total_without_tax() + order.wk_voucher_value
                                                    total_voucher_per_order_line = (price_unit / total_order_without_voucher) * amount_voucher
                                                    total_voucher_per_order_line = round_pr(total_voucher_per_order_line, currency_rounding)
                                                    base = price_unit - total_voucher_per_order_line

                                                    if (current_voucher && j !== 0) {
                                                        base += tax_amount
                                                        base = round_pr(base, currency_rounding)
                                                    }
                                                }
                                            }
                                        }

                                        tax_amount = order_line._compute_all(current_tax, base, quantity);
                                        tax_amount = round_pr(tax_amount, currency_rounding_bak);
                                        // tax_amount = round_pr(tax_amount, 1); //SET ROUNDING VALUE OF TAX AMOUNT

                                        if (current_tax.price_include) {
                                            base -= tax_amount;
                                        }

                                        if (current_tax.include_base_amount) {
                                            base += tax_amount;
                                        }
                                    }

                                    if (!list_of_taxes.length > 0) {
                                        list_of_taxes.push({
                                            tax_id: current_tax.id,
                                            tax_name: current_tax.name,
                                            tax_amount: tax_amount
                                        })
                                    }
                                    else if (list_of_taxes.length > 0) {
                                        list_of_taxes_id = list_of_taxes.map(tax => tax.tax_id)
                                        if (!list_of_taxes_id.includes(tax_id)) {
                                            list_of_taxes.push({
                                                tax_id: current_tax.id,
                                                tax_name: current_tax.name,
                                                tax_amount: tax_amount
                                            })
                                        }

                                        else if (list_of_taxes_id.includes(tax_id)) {
                                            for (var k = 0; k < list_of_taxes.length; k++) {
                                                if (list_of_taxes[k].tax_id === tax_id) {
                                                    list_of_taxes[k].tax_amount += tax_amount
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            return list_of_taxes
        },
        set_allow_to_validate_payment: function(condition) {
            this.allow_to_validate_payment = condition
            this.trigger('change')
        },
        get_allow_to_validate_payment: function() {
            return this.allow_to_validate_payment
        },
        set_allow_press_payment_numpad: function(condition) {
            this.allow_press_payment_numpad = condition
            this.trigger('change')
        },
        set_department_expense_office_check_pricing: function() {
            var order = this
            if (!!order.employee_id || !!order.department_id) {
                order.orderlines.forEach(function(line) {
                    var originalPrice
                    if(!line.price_manually_set){
                        originalPrice = line.product.get_price(line.order.pricelist, line.get_quantity());
                    } else {
                        originalPrice = line.get_unit_price()
                    }
                    var itemCost = line.product.standard_price
                    if (core.debug) {
                        console.log('name: ', line.product.display_name, ' - price: ', originalPrice, ' - item cost: ', itemCost)
                    }
                    // backup current price and cost
                    line.set_cost_and_original_price(originalPrice, itemCost)
                    line.set_unit_price(itemCost)
                })
            }
        },
        cancel_department_expense_office_check: function() {
            var order = this
            order.orderlines.forEach(function(line) {
                // get price and cost from backup
                var originalPrice = line.get_original_price()
                var itemCost = line.get_item_cost()
                if (core.debug) {
                    console.log('reset - name: ', line.product.display_name, ' - price: ', originalPrice, ' - item cost: ', itemCost)
                }
                line.set_unit_price(originalPrice)
            })
        },
        set_discount_type: function(discount_type) {
            this.discount_type = discount_type
            this.trigger('change',this)
        },
        get_discount_type: function(){
            return this.discount_type;
        },
        set_discount_pct_global: function(discount_pct_global) {
            this.discount_pct_global = discount_pct_global
            this.trigger('change',this)
        },
        set_discount_amount_total: function(discount_amount_total) {
            this.discount_amount_total = discount_amount_total
            this.trigger('change',this)
        },
        get_discount_pct_global: function(){
            return this.discount_pct_global;
        },
        get_discount_amount_total: function(){
            return this.discount_amount_total;
        },
        recalculate_discount: function() {
            var self = this
            var order = this
            var grand_total_wo_tax = 0
            order.orderlines.forEach(function(line) {
                grand_total_wo_tax += line.price * line.get_quantity();
                });

            if (core.debug) {
                console.log('recalculate line discounts', order.get_list_of_taxes(), order.discount_type, self.discount_amount_total, grand_total_wo_tax)
            }
            order.orderlines.forEach(function(line) {
                if (order.discount_type == 'amount') {
                    lineTotalWoTax = line.price * line.get_quantity();
                    potongan = ( lineTotalWoTax / grand_total_wo_tax ) * self.discount_amount_total

                    line.set_discount_amount(potongan)
                    if (core.debug) {
                        console.log('new disc', line.get_unit_price(), line.price, line.get_price_with_tax(), line.get_quantity(), grand_total_wo_tax,
                        line.get_discount(), line.get_discount_amount(), line.order.discount_type)
                    }
                } else {
                    line.set_discount(self.discount_pct_global)
                }

            });
        },
        // saat menghapus item, rekalkulasi discount per line
        remove_orderline: function( line ){
            if (core.debug) {
                console.log('remove_orderline', line)
            }
            _super_order.remove_orderline.apply(this, arguments)
            this.recalculate_discount();
            if (this.orderlines.length == 0) {
                this.outlet_id = false;
            }
        },
        // saat menambah item baru, rekalkulasi discount per line
        add_product: function(product, options){
            if (core.debug) {
                console.log('add_product', product, options)
            }
            if (this.outlet_id && this.outlet_id != product.pos_categ_id[0]) {
                this.pos.gui.show_popup('error', {
                    title: _t('Outlet vs Product Restriction'),
                    body: _t(
                        'You cannot choose this product! Outlet vs POS Category is different! ' +
                        'Only products from the same outlet is allowed'
                    ),
                })
                return false;
            }
            _super_order.add_product.apply(this, arguments)
            this.recalculate_discount()

            if (!this.outlet_id) {
                this.outlet_id = product.pos_categ_id[0]
            }
        },
        add_orderline: function(line){
            if (core.debug) {
                console.log('add_orderline', line)
            }
            _super_order.add_orderline.apply(this, arguments)
            this.recalculate_discount()
        },
    })

    var _super_orderline = models.Orderline.prototype
    models.Orderline = models.Orderline.extend({
        initialize: function(attr,options) {
            _super_orderline.initialize.apply(this, arguments)
            this.custom_item_name = options.custom_item_name
            this.note = options.note
            this.itemCost = options.itemCost
            this.originalPrice = options.originalPrice
            this.discount_amount = options.discount_amount || 0

            return this;
        },
        export_as_JSON: function() {
            var json = _super_orderline.export_as_JSON.apply(this, arguments)
            json.custom_item_name = this.custom_item_name
            json.note = this.note
            json.itemCost = this.itemCost
            json.originalPrice = this.originalPrice
            json.discount_amount = this.discount_amount
            return json
        },
        init_from_JSON: function(json) {
            _super_orderline.init_from_JSON.apply(this, arguments)
            this.custom_item_name = json.custom_item_name
            this.note = json.note
            this.itemCost = json.itemCost
            this.originalPrice = json.originalPrice
            this.discount_amount = json.discount_amount
        },
        export_for_printing: function() {
            var json = _super_orderline.export_for_printing.apply(
                this,
                arguments
            )
            json.custom_item_name = this.custom_item_name
            json.note = this.note
            json.itemCost = this.itemCost
            json.originalPrice = this.originalPrice
            json.discount_amount = this.discount_amount
            return json
        },
        set_quantity: function(quantity, keep_price){
            _super_orderline.set_quantity.apply(
                this,
                arguments
            )
            this.order.recalculate_discount();
        },
        set_custom_item_name: function(newName) {
            this.custom_item_name = newName
            this.trigger('change',this)
        },
        get_display_name: function() {
            if (!!this.custom_item_name){
                return this.custom_item_name
            }
            else {
                return this.get_product().display_name
            }
        },
        set_discount_amount: function(discount_amount) {
            // calculate discount % base on this amount
            var rounding = this.pos.currency.rounding;
            var percent_disc = (discount_amount/(this.price * this.get_quantity()) ) * 100
            this.set_discount(percent_disc)
            this.discount_amount = round_pr(discount_amount, rounding)
            this.discountStr = '' + this.get_discount_amount();
            if (core.debug) {
                console.log('apply disc by amoount', this.discount_amount,
                    this.order.get_discount_type(), this.get_discount_str())
            }
            this.trigger('change',this)
        },
        get_discount_amount: function(){
            var digits = this.pos.dp['Product Price'];
            // round and truncate to mimic _symbol_set behavior
            return parseFloat(round_di(this.discount_amount || 0, digits).toFixed(digits));
        },
        get_tax_details: function() {
            if (_.values(this.pos.get_order().paymentlines._byId)[0]) {
                if (
                    _.values(this.pos.get_order().paymentlines._byId)[0]
                        .cashregister.journal.is_officer_check
                ) {
                    return 0
                } else if (
                    _.values(this.pos.get_order().paymentlines._byId)[0]
                        .cashregister.journal.is_department_expense
                ) {
                    return 0
                } else {
                    return this.get_all_prices().taxDetails
                }
            } else {
                return this.get_all_prices().taxDetails
                return this.get_all_prices().taxDetails
            }
        },
        compute_all: function(taxes, price_unit, quantity, currency_rounding, no_map_tax) {
            var self = this;
            var list_taxes = [];
            var currency_rounding_bak = currency_rounding;
            if (this.pos.company.tax_calculation_rounding_method == "round_globally"){
               currency_rounding = currency_rounding * 0.00001;
            }
            var total_excluded = round_pr(price_unit * quantity, currency_rounding);
            var total_included = total_excluded;
            var base = total_excluded;
            // custom code
            var service_amount = 0;
            var zero_tax_service = (!!self.order.department_id || !!self.order.employee_id) ? true : false
            if (!zero_tax_service) {
                // custom code - end
                var taxes_mapped = [];
                if (!no_map_tax){
                    _(taxes).each(function(tax){
                        // original code:
                        // _(self._map_tax_fiscal_position(tax)).each(function(tax){
                        //     taxes_mapped.push(tax);
                        // });
                        // custom code, bridge between old odoo vs new code (after bug fix)
                        var map_tax_list = []
                        var tax_fp = self._map_tax_fiscal_position(tax)
                        if (Array.isArray(tax_fp)) {
                            map_tax_list = tax_fp
                        }
                        else if (!!tax_fp) {
                            // not array (old odoo code, add it to a list)
                            map_tax_list.push(tax_fp)
                        }
                        _(map_tax_list).each(function(tax){
                            taxes_mapped.push(tax);
                        });
                        // end custom code
                    });
                } else {
                    taxes_mapped = taxes;
                }
                _(taxes_mapped).each(function(tax) {
                    if (tax.amount_type === 'group'){
                        var ret = self.compute_all(tax.children_tax_ids, price_unit, quantity, currency_rounding);
                        total_excluded = ret.total_excluded;
                        base = ret.total_excluded;
                        total_included = ret.total_included;
                        list_taxes = list_taxes.concat(ret.taxes);
                        // custom code
                        service_amount = ret.service_amount;
                        // custom code -- end
                    }
                    else {
                        var tax_amount = self._compute_all(tax, base, quantity);
                        tax_amount = round_pr(tax_amount, currency_rounding);

                        if (tax_amount){
                            if (tax.price_include) {
                                total_excluded -= tax_amount;
                                base -= tax_amount;
                            }
                            else {
                                total_included += tax_amount;
                            }
                            if (tax.include_base_amount) {
                                base += tax_amount;
                            }
                            // custom code
                            var current_service_amount = 0;
                            if (!!tax.is_service_charge) {
                                service_amount += tax_amount;
                                current_service_amount = tax_amount;
                            }
                            // custom code - end
                            var data = {
                                id: tax.id,
                                amount: tax_amount,
                                name: tax.name,
                                service_amount: current_service_amount,
                                // custom code
                                is_service_charge: tax.is_service_charge
                                // custom code - end
                            };
                            list_taxes.push(data);
                        }
                    }
                });
            }

//            if (core.debug) {
//                console.log('line-compute all',zero_tax_service, self.order.department_id,
//                    self.order.employee_id, taxes)
//                console.log('line-compute all: total include', total_included,
//                    'exclude', total_excluded, 'service', service_amount)
//            }

            return {
                taxes: list_taxes,
                total_excluded: round_pr(total_excluded, currency_rounding_bak),
                total_included: round_pr(total_included, currency_rounding_bak),
                // custom code
                service_amount: round_pr(service_amount, currency_rounding_bak)
            };
        },
        get_display_price: function(){
            // original code
            if (this.pos.config.iface_tax_included === 'total') {
                return this.get_price_with_tax();
            } else {
                // original code
                // return this.get_base_price();
                // custom code
                // display line subtotal before discount and before tax/service
                return this.get_all_prices().bruttoBeforeTax;
            }
        },
        get_all_prices: function(){
            // original code
            var price_unit = this.get_unit_price() * (1.0 - (this.get_discount() / 100.0));
            var taxtotal = 0;

            var product =  this.get_product();
            var taxes_ids = product.taxes_id;
            var taxes =  this.pos.taxes;
            var taxdetail = {};
            var product_taxes = [];

            _(taxes_ids).each(function(el){
                product_taxes.push(_.detect(taxes, function(t){
                    return t.id === el;
                }));
            });

            var all_taxes = this.compute_all(product_taxes, price_unit, this.get_quantity(), this.pos.currency.rounding);
            _(all_taxes.taxes).each(function(tax) {
                taxtotal += tax.amount;
                taxdetail[tax.id] = tax.amount;
            });

            // custom code
            var rounding = this.pos.currency.rounding;
            var line_net_before_tax = all_taxes.total_excluded;
            var line_brutto_before_tax = round_pr((line_net_before_tax * 100) / (100 - this.get_discount()), rounding);
            var line_disc_amount_before_tax = round_pr(line_brutto_before_tax - line_net_before_tax, rounding);
            // custom code - end
            return {
                // Total After discount and after tax/service
                "priceWithTax": all_taxes.total_included,
                // Total After Discount Before Tax/Service = priceWithoutTax
                "priceWithoutTax": all_taxes.total_excluded,
                "tax": taxtotal,
                "taxDetails": taxdetail,
                // custom code
                "serviceAmount": all_taxes.service_amount,
                "taxWithoutService": taxtotal - all_taxes.service_amount,
                // Sub Total Line sebelum discount dan sebelum kena pajak/service
                "bruttoBeforeTax": line_brutto_before_tax,
                // Amount discount sebelum kena pajak/service
                "lineDiscAmountBeforeTax": line_disc_amount_before_tax
                // custom code - end
            };
        },
        set_cost_and_original_price: function(price, itemCost){
            var digits = this.pos.dp['Product Price'];
            this.originalPrice = round_di(parseFloat(price) || 0, digits);
            this.itemCost = round_di(parseFloat(itemCost) || 0, digits);
            this.trigger('change', this);
        },
//        // changes the base price of the product for this orderline
//        set_unit_price: function(price){
//            this.order.assert_editable();
//            this.price = round_di(parseFloat(price) || 0, this.pos.dp['Product Price']);
//            this.trigger('change',this);
//        },
        get_original_price: function(){
            var digits = this.pos.dp['Product Price'];
            // round and truncate to mimic _symbol_set behavior
            return parseFloat(round_di(this.originalPrice || 0, digits).toFixed(digits));
        },
        get_item_cost: function(){
            var digits = this.pos.dp['Product Price'];
            // round and truncate to mimic _symbol_set behavior
            return parseFloat(round_di(this.itemCost || 0, digits).toFixed(digits));
        },
    })

    var _super_paymentline = models.Paymentline.prototype
    models.Paymentline = models.Paymentline.extend({
        initialize: function(attributes, options) {
            _super_paymentline.initialize.apply(this, arguments)
            this.adv_payment = options.adv_payment
            this.voucher_id = options.voucher_id
            this.issuer_type = options.issuer_type;
            this.issuer_type_name = options.issuer_type_name
            this.card_holder_name = options.card_holder_name;
            this.front_card_number = options.front_card_number;
            this.back_card_number = options.back_card_number;
            this.voucher_no = options.voucher_no
        },
        export_as_JSON: function() {
            var json = _super_paymentline.export_as_JSON.apply(this, arguments)
            json.adv_payment = this.adv_payment
            json.voucher_id = this.voucher_id
            json.issuer_type = this.issuer_type;
            json.card_holder_name = this.card_holder_name;
            json.front_card_number = this.front_card_number;
            json.back_card_number = this.back_card_number;
            json.voucher_no = this.voucher_no
            return json
        },
        init_from_JSON: function(json) {
            _super_paymentline.init_from_JSON.apply(this, arguments)
            this.adv_payment = json.adv_payment
            this.voucher_id = json.voucher_id
            this.issuer_type = json.issuer_type
            this.card_holder_name = json.card_holder_name
            this.front_card_number = json.front_card_number
            this.back_card_number = json.back_card_number
            this.voucher_no = json.voucher_no
        },
        export_for_printing: function() {
            var json = _super_paymentline.export_for_printing.apply(
                this,
                arguments
            )
            json.voucher_id = this.voucher_id
            json.issuer_type = this.issuer_type;
            json.card_holder_name = this.card_holder_name
            json.front_card_number = this.front_card_number
            json.back_card_number = this.back_card_number
            json.voucher_no = this.voucher_no
            return json
        },
        get_new_amount: function() {
            if (this.cashregister.journal.is_officer_check) {
                if (this.pos.get_order() !== null) {
                    return this.pos.get_order().get_total_without_tax()
                } else {
                    return this.amount
                }
            } else if (this.cashregister.journal.is_department_expense) {
                if (this.pos.get_order() !== null) {
                    return this.pos.get_order().get_total_without_tax()
                } else {
                    return this.amount
                }
            } else {
                return this.amount
            }
        }
    })

    screens.PaymentScreenWidget.include({
        init: function(parent, options) {
            var self = this
            this._super(parent, options)

            this.pos.bind(
                'change:selectedOrder',
                function() {
                    this.renderElement()
                    this.watch_order_changes()
                },
                this
            )
            this.watch_order_changes()

            this.inputbuffer = ''
            this.firstinput = true
            this.decimal_point = _t.database.parameters.decimal_point

            // This is a keydown handler that prevents backspace from
            // doing a back navigation. It also makes sure that keys that
            // do not generate a keypress in Chrom{e,ium} (eg. delete,
            // backspace, ...) get passed to the keypress handler.
            this.keyboard_keydown_handler = function(event) {
                if (self.gui.current_popup) {
                    if (!self.gui.current_popup.enable_keypress) {
                        if (event.keyCode === 8 || event.keyCode === 46) {
                            // Backspace and Delete
                            event.preventDefault()

                            // These do not generate keypress events in
                            // Chrom{e,ium}. Even if they did, we just called
                            // preventDefault which will cancel any keypress that
                            // would normally follow. So we call keyboard_handler
                            // explicitly with this keydown event.
                            self.keyboard_handler(event)
                        }
                    }
                }
            }

            // This keyboard handler listens for keypress events. It is
            // also called explicitly to handle some keydown events that
            // do not generate keypress events.
            this.keyboard_handler = function(event) {
                if (self.gui.current_popup) {
                    if (!self.gui.current_popup.enable_keypress) {
                        if (
                            BarcodeEvents.$barcodeInput &&
                            BarcodeEvents.$barcodeInput.is(':focus')
                        ) {
                            return
                        }

                        var key = ''

                        if (event.type === 'keypress') {
                            if (event.keyCode === 13) {
                                // Enter
                                self.validate_order()
                            } else if (
                                event.keyCode === 190 || // Dot
                                event.keyCode === 110 || // Decimal point (numpad)
                                event.keyCode === 188 || // Comma
                                event.keyCode === 46
                            ) {
                                // Numpad dot
                                key = self.decimal_point
                            } else if (
                                event.keyCode >= 48 &&
                                event.keyCode <= 57
                            ) {
                                // Numbers
                                key = '' + (event.keyCode - 48)
                            } else if (event.keyCode === 45) {
                                // Minus
                                key = '-'
                            } else if (event.keyCode === 43) {
                                // Plus
                                key = '+'
                            }
                        } else {
                            // keyup/keydown
                            if (event.keyCode === 46) {
                                // Delete
                                key = 'CLEAR'
                            } else if (event.keyCode === 8) {
                                // Backspace
                                key = 'BACKSPACE'
                            }
                        }

                        self.payment_input(key)
                        event.preventDefault()
                    }
                }
            }

            this.pos.bind(
                'change:selectedClient',
                function() {
                    self.customer_changed()
                },
                this
            )
        },

        click_back: function(){
            var self = this
            var order = this.pos.get_order()
            if (core.debug) {
                console.log('back to order screen')
            }
            if (!!order.employee_id || !!order.department_id) {
                // if total COST = 0 in department expense/office check, clicking back button should delete payment line!
                var lines = order.get_paymentlines();
                lines.forEach(function(line) {
                    if ((!!line.cashregister.journal.is_department_expense
                                || !!line.cashregister.journal.is_officer_check)
                            && line.get_amount() == 0) {
                        self.click_delete_paymentline(line.cid)
                    }
                })
            }
            this._super()
            // this.gui.show_screen('products');
        },
        click_paymentmethods: function(id) {

            // get selected payment method
            // original code
            var cashregister = null
            for (var i = 0; i < this.pos.cashregisters.length; i++) {
                if (this.pos.cashregisters[i].journal_id[0] === id) {
                    cashregister = this.pos.cashregisters[i]
                    break
                }
            }
            // custom code
            order  = this.pos.get_order()
            var orderResidual = order.get_due()
            if (parseFloat(orderResidual).toPrecision(2) <= 0) {
                this.pos.gui.show_popup('error', {
                    title: _t('Full Payment'),
                    body: _t(
                        'The payment has been paid off'
                    ),
                })
                return
            }
            order.selected_cashregister = cashregister
            var paymentlines = _.values(this.pos.get_order().paymentlines._byId)

            // validate payment point (if applicable)
            if (cashregister.journal.is_point && !this.check_payment_point(paymentlines, cashregister)) {
                // stop, payment point tidak boleh dilanjutkan, krn tidak memenuhi syarat di pengecekan.
                return;
            }

            // validate whether split payment is allowed (multiple payment), if not, stop
            is_split_payment_allowed = true
            if (paymentlines[0]) {
                // some payment already exists
                // check if split payment allowed split or not
                is_split_payment_allowed = paymentlines[0].cashregister.journal.split_payment
                if (!is_split_payment_allowed) {
                    // split payment not allowed on existing payment
                    journal_name = paymentlines[0].cashregister.journal.name
                }
                else {
                    // existing payment allowed split, then check new payment
                    is_split_payment_allowed = cashregister.journal.split_payment
                    journal_name = cashregister.journal.name
                }
                if (!is_split_payment_allowed){
                    // split payment not allowed
                    this.gui.show_popup('error', {
                        title: _t('Payment Method Restriction'),
                        body: _t(
                            'You cannot choose this payment method, split payment not allowed for ' +
                            journal_name
                        ),
                    })
                    // stop, split payment not allowed
                    return;
                }
            }

            this.pos.payment_widget = this

            if (cashregister.journal.is_officer_check) {
                var self = this
                var list = []
                for (var i = 0; i < this.pos.employee.length; i++) {
                    var employee = this.pos.employee[i]
                    if (employee.is_officer_check) {
                        list.push({
                            label: employee.name,
                            item: employee,
                        })
                    }
                }
                var order = self.pos.get_order()

                self.gui.show_popup('selection', {
                    title: _t('Choose Employee'),
                    list: list,
                    confirm: function(item) {
                        var employee_id = item

                        order.set_employee(employee_id)
                        order.set_department_expense_office_check_pricing()

                        order.set_allow_press_payment_numpad(false)

                        order.add_paymentline(cashregister)
                        self.reset_input()
                        self.render_paymentlines()
                    },
                    is_selected: function(employee_id) {
                        if (self.pos.get_order().get_employee().employee_id) {
                            return (
                                employee_id.id ===
                                order.get_employee().employee_id
                                    .id
                            )
                        } else {
                            return false
                        }
                    },
                })
            }
            else if (cashregister.journal.is_department_expense) {
                var self = this
                var list = []
                for (var i = 0; i < this.pos.department.length; i++) {
                    var department = this.pos.department[i]
                    if (department.allow_pos_expense) {
                        list.push({
                            label: department.name,
                            item: department,
                        })
                    }
                }

                self.gui.show_popup('selection', {
                    title: _t('Choose Department'),
                    list: list,
                    confirm: function(item) {
                        var department_id = item

                        order.set_department(department_id)

                        order.set_department_expense_office_check_pricing()

                        order.set_allow_press_payment_numpad(false)

                        order.add_paymentline(cashregister)
                        self.reset_input()
                        self.render_paymentlines()
                    },
                    is_selected: function(department_id) {
                        if (self.pos.get_order().get_department().department_id) {
                            return (
                                department_id.id ===
                                self.pos.get_order().get_department()
                                    .department_id.id
                            )
                        } else {
                            return false
                        }
                    },
                })
            }
            else if (cashregister.journal.is_city_ledger) {
                var self = this
                var list = []
                for (var i = 0; i < this.pos.partners.length; i++) {
                    var partner = this.pos.partners[i]
                    if (partner.allow_use_city_ledger) {
                        list.push({
                            label: partner.name,
                            item: partner,
                        })
                    }
                }
                self.gui.show_popup('selection-search', {
                    title: _t('Choose Customer'),
                    list: list,
                    confirm: function(item) {
                        var order = self.pos.get_order()
                        var customer_id = item
                        order.set_customer(customer_id)

                        order.set_allow_press_payment_numpad(true)

                        order.add_paymentline(cashregister)
                        self.reset_input()
                        self.render_paymentlines()
                    },
                    is_selected: function(customer_id) {
                        var order = self.pos.get_order()
                        if (order.get_customer().customer_id) {
                            return (
                                customer_id.id ===
                                order.get_customer().customer_id
                                    .id
                            )
                        }
                    },
                })
            }
            else if (cashregister.journal.is_charge_room) {
                var self = this

                self.gui.show_popup('charge-room', {
                    title: _t('Charge to Room'),
//                    confirm: function() {
//                        var order = self.pos.get_order()
//                        var selected_folio = $('#folio').val()
//                        var room_number = $('#room-number').val()
//
//                        order.set_allow_press_payment_numpad(true)
//
//                        if (order.get_folio_data().folios) {
//                            var folio_owner = order.get_folio_data().folios.GuestName || ''
//                        }
//
//                        else if (order.get_folio().folio_owner) {
//                            var folio_owner = order.get_folio().folio_owner || ''
//                        }
//
//                        order.set_folio(selected_folio, room_number, folio_owner)
//                        self.gui.close_popup()
//
//                        order.add_paymentline(cashregister)
//                        self.reset_input()
//                        self.render_paymentlines()
//                    },
                })
            }
            else if (cashregister.journal.is_advance_payment) {
                var self = this
                var order = this.pos.get_order()
                var full_used_adv_payment = false
                order.adv_payment = false
                order.adv_payment_partner = false
                order.adv_payment_amount = 0
                order.adv_payment_residual = 0
                order.adv_payment_deposit = false
                order.used_adv_payment = []
                // order.list_of_adv_payments already set on AdvancePaymentPopup show method
                // order.list_of_adv_payments = this.pos.payment

                self.gui.show_popup('advance-payment', {
                    title: _t('Choose Payment'),
                    confirm: function() {
                        var advancePaymentId = parseInt(this.$('#payment').val())
                        var partnerPayment = parseInt(this.$('#partner').val())
                        var accountPayment = parseInt(this.$('#account').val())
                        var originalDepositAmount = parseFloat(this.$('#amount').val().replace(/,/g, ''))
                        var residualPayment = parseFloat(this.$('#residual').val().replace(/,/g, ''))
                        var depositTypeId = parseInt(this.$('#deposit').val())
                        var newPaymentAmount = parseFloat(this.$('#payment-amount').val().replace(/,/g, ''))

                        order.set_allow_press_payment_numpad(false)

                        if (!(advancePaymentId && partnerPayment && newPaymentAmount)) {
                            self.gui.show_popup('error', {
                                title: _t('Invalid Value'),
                                body: _t(
                                    'You must fill all the field required'
                                ),
                            })
                            // stop
                            return;
                        }
                        var orderResidual = order.get_due();
                        if (newPaymentAmount > residualPayment || newPaymentAmount > orderResidual) {
                            var maxPayment = residualPayment < orderResidual ? residualPayment : orderResidual
                            self.gui.show_popup('error', {
                                title: _t('Invalid Value'),
                                body: _t(
                                    'Maximum payment allowed is ' +
                                    maxPayment.toString().replace(/(\d)(?=(\d\d\d)+(?!\d))/g, "$1,")
                                ),
                            })
                            // stop
                            return;
                        }

                        order.set_payment(advancePaymentId, partnerPayment,
                            accountPayment, originalDepositAmount,
                            residualPayment, depositTypeId,
                            newPaymentAmount)

                        current_adv_payment = false
                        adv_payment_amount_used = newPaymentAmount
                        var newAdvPaymentResidual = residualPayment - newPaymentAmount

                        console.log('adv payment selected', advancePaymentId, residualPayment, newAdvPaymentResidual, newPaymentAmount, adv_payment_amount_used)

                        for (var i = 0; i < self.pos.payment.length; i++) {
                            if (self.pos.payment[i].id === order.adv_payment) {
                                // current_adv_payment = _.cloneDeep(self.pos.payment[i])
                                current_adv_payment = JSON.parse(JSON.stringify(self.pos.payment[i]));
                                // update residual amount on adv payment data (stored in self.pos.payment)
                                self.pos.payment[i].residual_temp -= newPaymentAmount
                            }
                        }
                        // TODO: check the usage of order.list_of_adv_payments vs this.pos.payment
                        //    duplicate use?
                        //  Note: this.pos.payment akan terisi ulang dari data backend odoo saat reload?
                        //    order.list_of_adv_payments --> data ada di cache db browser
                        for (var i = 0; i < order.list_of_adv_payments.length; i++) {
                            if (order.list_of_adv_payments[i].id === order.adv_payment) {
                                order.list_of_adv_payments[i].residual_temp -= newPaymentAmount
                            }
                        }
                        order.used_adv_payment.push({
                            current_adv_payment: current_adv_payment,
                            adv_payment_amount_used: newPaymentAmount,
                            payment_residual: newAdvPaymentResidual,
                            full_used_adv_payment: newAdvPaymentResidual == 0 ? true : false
                        })

                        // order.set_list_adv_payment(order.list_of_adv_payments)
                        self.gui.close_popup()
                        self.pos.get_order().add_paymentline(cashregister)
                        self.reset_input()
                        self.render_paymentlines()

                    },
                })
            }
            else if (cashregister.journal.is_point) {
                var self = this
                var order = this.pos.get_order()

                if (order.my_value_data) {
                    self.gui.show_popup('my-value-payment', {
                        title: _t('MyValue'),
                        confirm: function() {
                            // var my_value_points = parseInt(this.$('#my-value-points').val()) || 0.0
                            var my_value_points = parseFloat(this.$('#my-value-points').val().replace(/\./g,'')) || 0.0
                            var my_value_points_used = parseFloat(this.$('#my-value-points-used').val().replace(/\./g,'')) || 0.0
                            var minimum_redeem_points = this.pos.config.myvalue_minimum_redeem_point || 0.0

                            order.set_allow_press_payment_numpad(false)

                            if (my_value_points_used > my_value_points) {
                                self.pos.gui.show_popup('error',{
                                    'title':_t('MyValue Points Error'),
                                    'body': _t('You cannot input points more than points available.'),
                                });
                            }

                            else if (my_value_points_used < minimum_redeem_points) {
                                var alert = `You cannot input points less than ${minimum_redeem_points}` + '  ' + '(minimum redeem points).';
                                self.pos.gui.show_popup('error',{
                                    'title':_t('MyValue Points Error'),
                                    'body': _t(alert),
                                });
                            }

                            else if (my_value_points_used > order.get_due()) {
                                self.pos.gui.show_popup('error',{
                                    'title':_t('MyValue Points Error'),
                                    'body': _t('You cannot input MyValue Points more than total amount of transaction'),
                                });
                            }

                            else {
                                order.set_my_value_points(my_value_points, my_value_points_used)
                                this.gui.close_popup()
                                self.pos.get_order().add_paymentline(cashregister)
                                self.reset_input()
                                self.render_paymentlines()
                            }
                        },
                    })
                }
                else {
                    self.pos.gui.show_popup('error', {
                        title: _t('MyValue ID'),
                        body: _t(
                            'This payment method only can be used only if you use MyValue ID'
                        ),
                    })
                }
            }
            else if (cashregister.journal.is_voucher) {
                this.gui.show_popup('kg-voucher', {
                    title: _t('Select Voucher'),
                    cheap: true,
                })
            }
            else if (cashregister.journal.type === 'bank') {
                this.gui.show_popup('credit-card', {
                    title: _t('Credit Card Info'),
                    cheap: true,
                })
            } else {
                this.pos.get_order().set_allow_press_payment_numpad(true)

                this.pos.get_order().add_paymentline(cashregister)
                this.reset_input()
                this.render_paymentlines()
            }

        },
        stringToFloat: function(value) {
            // dari 123,567,323.00 jadi: 123567323.00
            return parseFloat(value.replace(/\,/g,'')) || 0.0
        },
        click_delete_paymentline: function(cid){
            var self = this
            var order = this.pos.get_order()
            var lines = order.get_paymentlines();

            for ( var i = 0; i < lines.length; i++ ) {
                if (lines[i].cid === cid) {
                    adv_payment_id = false

                    if (lines[i].cashregister.journal.is_advance_payment) {
                        adv_payment_id = lines[i].adv_payment
                    } else if (lines[i].cashregister.journal.is_charge_room) {
                        // check if payment from folios, remove folio info from order and payment!
                        order.set_folio_data([])
                        order.set_folio(false, false, false)
                    } else if (lines[i].cashregister.journal.is_department_expense) {
                        order.set_department(null)
                        order.cancel_department_expense_office_check()
                    } else if (lines[i].cashregister.journal.is_officer_check) {
                        order.set_employee(null)
                        order.cancel_department_expense_office_check()
                    }

//                    console.log('delete payment', lines[i])

                    var deleted_adv_payment_id = false
                    var after_delete_adv_payments = false

                    order.remove_paymentline(lines[i]);
                    this.reset_input();
                    this.render_paymentlines();

                    if (adv_payment_id) {
                        for (var i = 0; i < order.used_adv_payment.length; i++) {
                            if (order.used_adv_payment[i].current_adv_payment.id === adv_payment_id[0]) {
                                deleted_adv_payment_id = order.used_adv_payment[i].current_adv_payment.id
                                for (var k = 0; k < self.pos.payment.length; k++) {
                                    if (self.pos.payment[k].id === adv_payment_id[0]) {
                                        // update residual amount on adv payment data (stored in self.pos.payment)
                                        self.pos.payment[k].residual_temp += order.used_adv_payment[i].adv_payment_amount_used
                                    }
                                }
                                var adv_payment_found_in_list = false
                                for (var j = 0; j < order.list_of_adv_payments.length; j++) {
                                    if (order.list_of_adv_payments[j].id === deleted_adv_payment_id) {
                                        order.list_of_adv_payments[j].residual_temp += order.used_adv_payment[i].adv_payment_amount_used
                                        // order.used_adv_payment[i].adv_payment_amount_used
                                        adv_payment_found_in_list = true
                                    }
                                }
                                if (!adv_payment_found_in_list) {
                                    order.list_of_adv_payments.push(
                                        order.used_adv_payment[i].current_adv_payment
                                    )
                                }
                            }
                        }

                        if (deleted_adv_payment_id) {
                            after_delete_adv_payments = order.used_adv_payment.filter(pay => pay.current_adv_payment.id != deleted_adv_payment_id)
                            order.used_adv_payment = after_delete_adv_payments
                        }
                        console.log('used adv payment after delete ', order.used_adv_payment)
                    }
                    return;
                }
            }
        },
        payment_input: function(input) {
            var order = this.pos.get_order()
            var paymentlist = _.values(this.pos.get_order().paymentlines._byId)
            var split_payment = false

            // for (var i = 0; i < paymentlist.length; i++) {
            //     if (paymentlist[i].cashregister.journal.split_payment) {
            //         split_payment = true
            //     }
            // }

            // if (split_payment) {
            //     this._super(input)
            // }

            if (order.allow_press_payment_numpad) {
                this._super(input)
            }
        },
        check_payment_point: function(paymentlines, cashregister) {
            if (!cashregister.journal.is_point) {
                // bukan payment point, tidak perlu dicek lebih jauh
                return true
            }
//            console.log (this.pos.config)
            if (!this.pos.config.my_value_outlet_id) {
                this.gui.show_popup('error', {
                    title: _t('Payment Method Restriction'),
                    body: _t(
                        'You cannot choose this payment, MyValue Outlet ID is not defined in POS Config!'
                    ),
                })
                return false;
            }
            var point_already_exists = false;
            if (cashregister.journal.is_point && paymentlines.length > 0) {
                // for payment with point, only single point payment is allowed
                paymentlines.forEach((pl) => {
                    // console.log(pl.cashregister.journal.id)
                    if (pl.cashregister.journal.id == cashregister.journal.id) {
                        this.gui.show_popup('error', {
                            title: _t('Payment Method Restriction'),
                            body: _t(
                                'You cannot choose this payment again, already exists.'
                            ),
                        })
                        point_already_exists = true;
                    }
                })
            }
            if (point_already_exists) {
                // payment point tidak boleh lebih dari 1, stop
                return false
            }
            return true;
        },
        validate_order: function(force_validation) {
            // Original Code:
            // if (self.order_is_valid(force_validation)) {
            //     self.finalize_validation();
            // }

            // TODO: aan: moved all code related MyValue to my_value.js
            var self = this
            var _super_method = this._super.bind(this);
            var order = self.pos.get_order()

            self.pos.allowed_to_access_payment = false
            self.pos.allowed_to_delete = false

            if (!order.my_value_data) {
                // no my value id in transaction
                _super_method(force_validation)
                // this._super(force_validation)
            }
            else {
                // MY VALUE ID INCLUDED IN TRANSACTION
                var amount_untaxed = order.get_total_without_tax()
                var my_value_points_used = order.my_value_points_used ? order.my_value_points_used : 0

                // CHECK IF POINT PAYMENT IS IN THE PAYMENTLINE
                var point_payment = false
                var voucher_payment = false
                var voucher_payment_amount = 0
                var payment_lines = order.get_paymentlines()
                if (!!payment_lines && payment_lines.length > 0) {
                    point_payment = payment_lines.filter(pay => pay.cashregister.journal.is_point)[0]
                    voucher_payment = payment_lines.filter(pay => pay.cashregister.journal.is_voucher)[0]
                    if(voucher_payment){
                        voucher_payment_amount = voucher_payment.amount
                    }
                }
                var my_value_earn_amount = amount_untaxed - my_value_points_used - voucher_payment_amount

                my_value_earn_amount = my_value_earn_amount > 0 ? my_value_earn_amount : 0
                var my_value_points_data = {
                    'my_value_data': order.my_value_data,
                    'my_value_id': order.my_value_id,
                    'my_value_points': order.my_value_points,
                    'my_value_points_used': my_value_points_used,
                    'voucher_payment_amount': voucher_payment_amount,
                    'my_value_earn_amount': my_value_earn_amount,
                    'my_value_outlet_id': order.pos.config.my_value_outlet_id,
                    'amount_untaxed': amount_untaxed,
                    'amount_total': order.get_total_with_tax(),
                    'transaction_date': (new Date()).toISOString(),
                    'order_name': order.name + '/S/' + order.pos_session_id,
                }


                if (point_payment) {
                    // POINT USED AS PAYMENT METHOD -- Process Redeem - then earning later on (inside this function)
                    self.send_redeem_points(my_value_points_data, force_validation, _super_method);
                }
                else {
                    // NO POINT USED AS PAYMENT METHOD BUT THE TRANSACTION INCLUDE MY VALUE ID
                    // process earning only
                    self.send_earn_points(my_value_points_data, force_validation, _super_method);
                }
            }
        },
        send_redeem_points: function(my_value_points_data, force_validation, _super_method) {
            // TODO: aan: moved all code related MyValue to my_value.js
            var self = this
            var order = self.pos.get_order()

            order.set_my_value_redeem_response(false)

            if (core.debug) {
                console.log('into function redeem points')
            }
            rpc.query({
                model: 'pos.helpers',
                method: 'send_redeem_points',
                args: [my_value_points_data],
            }).then(function(response) {
                if (response) {
                    if (core.debug) {
                        console.log('redeem_response_before', order.my_value_redeem_response)
                        console.log('current_redeem_response', response)
                    }

                    order.set_my_value_redeem_response(response)
                    if (core.debug) {
                        console.log('redeem_response_after', order.my_value_redeem_response)
                    }

                    // CHECK IF RESPONSE IS NOT SUCCESS RETURN TRANSACTION REDEEM ERROR, ELSE CONTINUE TO NEXT FUNCTION
                    if (response.code !== 200) {
                        // redeem failed
                        var myvalue_response_message = '';
                        if (response.Data && response.Data.response && response.Data.response.Message) {
                            myvalue_response_message = response.Data.response.Message
                        }
                        return self.gui.show_popup('error', {
                            title: _t('Redeem Transaction'),
                            body: _t(
                                'Redeem transaction fail. Message: ' + myvalue_response_message
                            ),
                        });
                    } else {
                        // redeem success
                        non_point_payment = order.get_paymentlines().filter(payment => !payment.cashregister.journal.is_point)
                        // CHECK IF THERE IS NON POINT PAYMENT METHOD INCLUDED IN THIS TRANSACTION, THEN IT WILL USED AS EARN POINTS IN PMS
                        if (!!non_point_payment && non_point_payment.length > 0) {
                            // continue to process earning
                            self.send_earn_points(my_value_points_data, force_validation, _super_method)
                        }
                        // CHECK IF THERE IS NO OTHER PAYMENT EXCEPT POINT PAYMENT IN TRANSACTION, THEN CONTINUE TO VALIDATE THE TRANSACTION
                        else {
                            _super_method(force_validation)
                        }
                    }
                }
            });
        },
        send_earn_points: function(my_value_points_data, force_validation, _super_method) {
            // TODO: aan: moved all code related MyValue to my_value.js
            var self = this
            var order = self.pos.get_order()
            var my_value_outlet_id = order.pos.config.my_value_outlet_id
            var my_value_earn_amount = my_value_points_data.my_value_earn_amount
            order.set_my_value_earn_response(false, 0, my_value_outlet_id)

            if (core.debug) {
                console.log('into function earn points', my_value_points_data)
            }
            rpc.query({
                model: 'pos.helpers',
                method: 'send_earn_points',
                args: [my_value_points_data],
            }).then(function(response) {
                // send_earn_points -- no error, got response
                if (response) {
                    if (core.debug) {
                        // console.log('earn_response_before', order.my_value_earn_response)
                        console.log('current_earn_response', response)
                    }

                    order.set_my_value_earn_response(
                        response, my_value_earn_amount, my_value_outlet_id)
                    if (core.debug) {
                        console.log('earn_response_after', order.my_value_earn_response)
                    }
                }
                // DOESN'T CARE ABOUT THE RESPONSE MESSAGE SUCCESS OR NOT, continue validation
                _super_method(force_validation)
            }, function(err) {
                // error/failed on send_earn_points
                // DOESN'T CARE ABOUT THE RESPONSE MESSAGE SUCCESS OR NOT, continue validation
                _super_method(force_validation)
            })
        },
        click_paymentline: function(cid){
            var order = this.pos.get_order()
            var lines = this.pos.get_order().get_paymentlines();
            for ( var i = 0; i < lines.length; i++ ) {
                if (lines[i].cid === cid) {

                    // CUSTOM CODE TO CHECK THE PAYMENT METHOD IN PAYMENTLINE
                    if (lines[i].cashregister.journal.is_point || lines[i].cashregister.journal.is_advance_payment) {
                        order.set_allow_press_payment_numpad(false)
                    }
                    else if (!lines[i].cashregister.journal.split_payment) {
                        order.set_allow_press_payment_numpad(false)
                    }
                    else {
                        order.set_allow_press_payment_numpad(true)
                    }
                    // END OF CUSTOM CODE

                    this.pos.get_order().select_paymentline(lines[i]);
                    this.reset_input();
                    this.render_paymentlines();
                    return;
                }
            }
        },
    })

    screens.OrderWidget.include({
        update_summary: function(){
            this._super()
            // custom code
            order = this.pos.get_order()
            if (order) {
                var all_order_totals = order.get_all_order_totals()
                var service = all_order_totals.totalServiceAmount
                var tax_without_service = all_order_totals.totalTaxWithoutService

                $("#sub-total-info").html(this.format_currency(all_order_totals.totalBeforeTax));
                $("#discount-info").html(this.format_currency(all_order_totals.totalDiscAmountBeforeTax));
                $("#service-charge-info").html(this.format_currency(service));
                $("#tax-without-service-info").html(this.format_currency(tax_without_service));
            }

            $('#taxes').empty()

//            var total = 0.0
//            var total_tax = 0.0

            // set data list of taxes (to be send to back end)
            var list_of_taxes = order.get_list_of_taxes()
            order.list_of_taxes = list_of_taxes
//
//            if (list_of_taxes) {
//                for (var i = 0; i < list_of_taxes.length; i++) {
//                    $('#taxes').append(
//                        `
//                        <div class="list-taxes">
//                            <span>${list_of_taxes[i].tax_name}</span>
//                            <span> : </span>
//                            <span>${this.format_currency(list_of_taxes[i].tax_amount)}</span>
//                        </div>
//                        `
//                    )
//                    total_tax += list_of_taxes[i].tax_amount
//                }
//            }
//
//            if (document.getElementById('taxes')){
//                $('#list_of_taxes').empty()
//            }
//
//            if (order) {
//                if (order.get_orderlines().length) {
//                    total = total_tax + order.get_total_without_tax()
//                    this.el.querySelector('.summary .total > .value').textContent = this.format_currency(total);
//                }
//            }

            // end of custom code
        },
    })
})
