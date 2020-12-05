odoo.define('kg_pos.product_custom_name_notes', function(require) {
    'use strict'

    var core = require('web.core');
    var _t = core._t;
    var models = require('point_of_sale.models')
    var screens = require('point_of_sale.screens')
    var gui = require('point_of_sale.gui')
    var popups = require('point_of_sale.popups')

    models.load_fields("product.product",
        ['allow_custom_item','allow_open_price', 'standard_price', 'pos_categ_id', 'main_category']);

    // handle allow open price product and discount numpad
    screens.NumpadWidget.include({
        clickChangeMode: function(event) {
            var newMode = event.currentTarget.attributes['data-mode'].nodeValue
            var self = this

            var order = self.pos.get_order()
            this.discount_amount_total = order.discount_amount_total
            this.discount_pct_global = order.discount_pct_global
            if (newMode === 'price') {
                var selectedOrderline = this.pos.get_order().get_selected_orderline()
                if (selectedOrderline.product.allow_open_price) {
                    selectedOrderline.price_manually_set = true
                    return this.state.changeMode(newMode)
                }
            }
            else if (newMode === 'discount') {
                if (this.discount_pct_global == 0 && this.discount_amount_total == 0){
                    return this.state.changeMode(newMode)
                }
            }
            else {
                return this.state.changeMode(newMode)
            }
        },
    })

    var OpenCustomItemWidget = popups.extend({
        template: 'OpenCustomItemWidget',
        show: function(options) {
            var self = this
            options = options || {}
            this._super(options)

            var order = self.pos.get_order()
            this.selectedOrderline = order.get_selected_orderline()
            this.price = this.numberWithCommas(this.selectedOrderline.price)
            this.custom_item_name = this.selectedOrderline.custom_item_name
            this.note = this.selectedOrderline.note
            this.product = this.selectedOrderline.product
            this.name = this.product.display_name
            this.allow_custom_item = this.product.allow_custom_item
            this.allow_open_price = this.product.allow_open_price

            this.renderElement()
        },
        click_confirm: function(event) {
            var newName = this.$('#custom-product-name').val()
            var newPrice = this.$('#new-price').val()
            var note = this.$('#note').val()

            this.selectedOrderline.set_custom_item_name(newName)
            this.selectedOrderline.set_note(note)
            if (!!this.product.allow_open_price) {
                if (newPrice !==  "" ) {
                    this.selectedOrderline.price_manually_set = true;
                    this.selectedOrderline.set_unit_price(newPrice);
                }
            }
            this.gui.close_popup()
        },
        numberWithCommas:function (number) {
            return number.toLocaleString("en")
        },
        stringToFloat: function(value) {
            // dari 123,567,323.00 jadi: 123567323.00
            return parseFloat(value.replace(/\,/g,'')) || 0.0
        },
    })   

    gui.define_popup({ name: 'custom-item-info', widget: OpenCustomItemWidget })

    var OpenCustomItemButton = screens.ActionButtonWidget.extend({
        template: 'OpenCustomItemButton',
        button_click: function() {
            var self = this
            var order = self.pos.get_order()
            this.selectedOrderline = order.get_selected_orderline()
            if (!!this.selectedOrderline) {
                this.product = this.selectedOrderline.product
    //            console.log('product', this.product)
                if (this.product.allow_custom_item || this.product.allow_open_price) {
                    this.gui.show_popup('custom-item-info', {
                        title: _t('Custom Item'),
                        cheap: true,
                    })
                }
            }

        },
        renderElement: function() {
            var self = this
            if (self.pos.config.iface_floorplan) {
                this._super()
            }
        },
    })

    screens.define_action_button({
        'name': 'OpenCustomItem',
        'widget': OpenCustomItemButton,
        'condition': function(){
            // return this.pos.config.module_pos_discount;
            return true;
        },
    });
    

})