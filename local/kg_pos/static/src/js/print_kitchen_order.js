odoo.define('kg_pos.print_kitchen_order', function (require) {
"use strict";

var core = require('web.core');
var screens = require('point_of_sale.screens');
var gui = require('point_of_sale.gui');

var QWeb = core.qweb;

var KitchenOrderScreenWidget = screens.ReceiptScreenWidget.extend({
    template: 'KitchenOrderScreenWidget',
    click_next: function(){
        this.gui.show_screen('products');
    },
    click_back: function(){

        this.gui.show_screen('products');
    },
    get_report_name: function() {
        return this.pos.config.kitchen_order_report_name
    },
    render_receipt: function(){
        this._super();
        this.$('.receipt-paymentlines').remove();
        this.$('.receipt-change').remove();
    },
    print_web: function(){
        window.print();
    },
});

gui.define_screen({name:'kitchen-bill', widget: KitchenOrderScreenWidget});

var KitchenOrderButton = screens.ActionButtonWidget.extend({
    template: 'KitchenOrderButton',
    print_xml: function(){
        var order = this.pos.get('selectedOrder');
        if(order.get_orderlines().length > 0){
            var receipt = order.export_for_printing();
            receipt.bill = true;
            this.pos.proxy.print_receipt(QWeb.render('KitchenOrderReceipt',{
                receipt: receipt, widget: this, pos: this.pos, order: order,
            }));
        }
    },
    button_click: function(){
        if (!this.pos.config.iface_print_via_proxy) {
            this.gui.show_screen('kitchen-bill');
        } else {
            this.print_xml();
        }
    },
});

screens.define_action_button({
    'name': 'print_kitchen_order',
    'widget': KitchenOrderButton,
    'condition': function(){ 
        return this.pos.config.kitchen_order_report_name;
    },
});

});
