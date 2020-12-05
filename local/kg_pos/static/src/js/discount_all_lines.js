odoo.define('kg_pos.pos_discount_all_lines', function (require) {
    "use strict";

    var core = require('web.core');
    var _t = core._t;
    var models = require('point_of_sale.models')
    var screens = require('point_of_sale.screens')
    var gui = require('point_of_sale.gui')
    var popups = require('point_of_sale.popups')

    var DiscountAmountWidget = popups.extend({
        template: 'DiscountAmountWidget',
        show: function(options) {
            var self = this
            options = options || {}
            this._super(options)

            var order = self.pos.get_order()
            this.discount_type = order.discount_type
            if (this.discount_type == 'amount'){
                this.discount_amount_total = order.discount_amount_total
            } else {
                this.discount_pct_global = order.discount_pct_global
            }
            this.renderElement()
        },
        click_confirm: function(event) {
            var self = this
            var amount_type = this.$("select[name=discount_type]").val()
            var disc_amount = parseFloat(this.$('#discount-amount').val() || 0);
            var amount_untaxed = order.get_subtotal()
            var potongan = 0
            var persen_potongan = 0

            if ( disc_amount == 0 ) {
                // clear discount
                order.set_discount_type(null)
                order.set_discount_amount_total(0)
                order.set_discount_pct_global(0)
                order.recalculate_discount()
            } else if (amount_type ==  "amount" && disc_amount > 0) {
                // by amount
                var order_total = order.get_total_with_tax()
                if (disc_amount > amount_untaxed ) {
                    // not allowed
                    this.gui.show_popup('error', {
                        title: _t('Invalid Value'),
                        body: _t(
                            'Maximum discount is ' + amount_untaxed
                        ),
                    })
                    return
                }
                order.set_discount_type("amount")
                order.set_discount_amount_total(disc_amount)
                order.recalculate_discount()
            } else if (amount_type ==  "pct" && disc_amount > 0) {
                    if ( disc_amount > '100' || disc_amount < '0' ) {
                        // not allowed
                        this.gui.show_popup('error', {
                            title: _t('Invalid Value'),
                            body: _t(
                                'Maximum discount is ' + 100 + '%'
                            ),
                        })
                        return
                    }
                order.set_discount_type("pct")
                order.set_discount_pct_global(disc_amount)
                order.recalculate_discount()

            }
            this.gui.close_popup()
        },

    })

    gui.define_popup({ name: 'discount-amount-info', widget: DiscountAmountWidget })

    var DiscountAmountButton = screens.ActionButtonWidget.extend({
        template: 'DiscountAmountButton',
        button_click: function() {
            var self = this
            var order = self.pos.get_order()
            this.gui.show_popup('discount-amount-info', {
                title: _t('Discount All Order'),
                cheap: true,
            })
        },
        renderElement: function() {
            var self = this
            if (self.pos.config.iface_floorplan) {
                this._super()
            }
        },
    })

    screens.define_action_button({
        'name': 'DiscountAmount',
        'widget': DiscountAmountButton,
        'condition': function(){
            // return this.pos.config.module_pos_discount;
            return true;
        },
    });


});
