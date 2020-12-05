odoo.define('point_of_sale.pos_orders', function(require) {
"use strict";

var PosBaseWidget = require('point_of_sale.BaseWidget');
var screens = require('point_of_sale.screens');
var gui = require('point_of_sale.gui');
var core = require('web.core');
var rpc = require('web.rpc');
var session = require('web.session');
var models = require('point_of_sale.models');
var PopupWidget = require('point_of_sale.popups');
var ScreenWidget = screens.ScreenWidget;
var ClientListScreenWidget = screens.ClientListScreenWidget;
var Backbone = window.Backbone;
var longpolling = require('pos_longpolling');
var QWeb = core.qweb;
var _t = core._t;

var PosModelSuper = models.PosModel;

var _super_order = models.Order.prototype

models.Order = models.Order.extend({
    initialize: function() {
        _super_order.initialize.apply(this, arguments)
        this.is_reservation = this.is_reservation || false;
        this.reservation_order_id = this.reservation_order_id || false;
        this.save_to_db()
    },
    export_as_JSON: function() {
        var json = _super_order.export_as_JSON.apply(this, arguments)

        json.is_reservation = this.is_reservation
        json.reservation_order_id = this.reservation_order_id

        return json
    },
    init_from_JSON: function(json) {
        _super_order.init_from_JSON.apply(this, arguments)

        this.is_reservation = json.is_reservation
        this.reservation_order_id = json.reservation_order_id
    },
    set_reservation_info: function(name, reservation_order_id) {
        this.name = name
        this.reservation_order_id = reservation_order_id;
        this.is_reservation = true
        this.trigger('change')
    }
})

models.load_models({
    model:  'kg.pos.order.reservation',
    fields: ['name', 'partner_id','date_order','date_order_tz','reservation_time_start','reservation_start_date','start_time_tz','end_time_tz','amount_total','pos_reference','lines','state','session_id','company_id','is_reservation','booking_phone_number','reserved_by','customer_count','state_reservation','reservation_pos_id','table_label'],
    domain: function(self) {return [
            ['company_id', '=', self.company && self.company.id || false]
            , ['reservation_pos_id', '=', self.config.id]
            , ['state_reservation', 'in', ['waiting_list','tentative','definite']]
//            , ['reservation_start_date', '=', (new Date()).toJSON().slice(0,10).replace(/-/g,'-')]
//            , ['reservation_time_start', '<=', (new Date()).toISOString()]
//            , ['reservation_time_end', '>=', (new Date()).toISOString()]
        ]},
    loaded: function(self, orders) {
        //self.orderReservations = orders
        // console.log('load reservation orders', session.company_id, session)
        self.orderReservations = [];
        // orders = orders.sort((a, b) => a.reservation_time_start - b.reservation_time_start || a.name - b.na);

        // filter by non stored field reservation_start_date, not working in domain, so we filter again here
        var d = new Date().toJSON().slice(0,10).replace(/-/g,'-');
        for (var i = 0; i < orders.length; i++) {
            if (orders[i].reservation_start_date == d) {
                self.orderReservations.push(orders[i])
            }
        }
        // console.log('load kg.pos.order.reservation', orders, 'loaded to: ', self.orderReservations)
    }
});

models.load_models({
    model:  'kg.pos.order.reservation.line',
    fields: ['id', 'order_id', 'product_id', 'qty', 'discount','price_subtotal_incl', 'price_unit'],
    domain: function(self) {return [
            ['order_id.company_id', '=', self.company && self.company.id || false]
            , ['order_id.reservation_pos_id', '=', self.config.id]
            , ['order_id.state_reservation', 'in', ['waiting_list','tentative','definite']]
//            , ['reservation_start_date', '=', (new Date()).toJSON().slice(0,10).replace(/-/g,'-')]
//            , ['reservation_time_start', '<=', (new Date()).toISOString()]
//            , ['reservation_time_end', '>=', (new Date()).toISOString()]
        ]},
    loaded: function(self, order_lines){
        self.orderReservationLines = order_lines;
        console.log('reservation_lines: ', order_lines.length, order_lines)
        }
    });

var OrderPopupWidget = PopupWidget.extend({
    template: 'OrderPopupWidget',
    show: function(options){
        var self = this;
        options = options || {};
        this._super(options);
        this.order = options.order || {};
        this.line = options.line;
        this.renderElement();
    },
    click_confirm: function(){
        var self = this;
        var current_order = self.pos.get_order();
        // updates status to checkin when booking is loaded marioardi
        console.log('confirm', current_order.id, this.order.id, current_order.name, this.order.name, current_order, this.order)
        current_order.set_reservation_info(this.order.name, this.order.id)

        console.log('confirm order selected info', this.order)

        rpc.query({
            model: 'kg.pos.order.reservation',
            method: 'set_check_in',
            args: [self.order.id]
         }).then(function (result) { 
            console.log('reservation checked in !');
        });

        this.line.removeClass('highlight');
        _.each(this.order.orderReservationLines, function(l){
            var product = self.pos.db.get_product_by_id(l['product_id']);
            // TODO: warn error if product is undefined (not found in this pos config!
            current_order.add_product(product,{ quantity: l['qty'], price: l['price_unit']});
            current_order.is_reservation = true;
        })
        if (this.order.partner_id){
            var partner = self.pos.db.get_partner_by_id(this.order.partner_id);
            current_order.set_client(partner);
            current_order.set_customer_count(this.order.customer_count);
            current_order.is_reservation = true;
        }

        this.gui.show_screen('products');
        // hide reservation button when order is loaded by mario ardi;
        document.getElementById('pos_order_list_button').style.display = "none";
    },
    click_cancel: function(){
        this._super();
        this.line.removeClass('highlight');
    },
});
gui.define_popup({name:'order', widget: OrderPopupWidget});

// POS Order Table Reservation Widget
var PosOrderScreenWidget = ScreenWidget.extend({
    template: 'PosOrderScreenWidget',
    back_screen:   'product',
    init: function(parent, options){
        var self = this;
        this._super(parent, options);
    },

    show: function(){
        var self = this;
        this._super();
        this.renderElement();
        this.$('.back').click(function(){
            self.gui.show_screen('products');
        });
        var orders = this.get_orders();
        this.render_list(orders);

        this.$('.order-list-contents').delegate('.order-line','click',function(event){
            self.line_select(event,$(this),parseInt($(this).data('id')));
        });

        var search_timeout = null;

        if(this.pos.config.iface_vkeyboard && this.chrome.widget.keyboard){
            this.chrome.widget.keyboard.connect(this.$('.searchbox input'));
        }

        this.$('.searchbox input').on('keyup',function(event){
            clearTimeout(search_timeout);
            var query = this.value;
            search_timeout = setTimeout(function(){
                self.perform_search(query,event.which === 13);
            },70);
        });

        this.$('.searchbox .search-clear').click(function(){
            self.clear_search();
        });
    },

    get_orders: function(){
        return this.gui.get_current_screen_param('orders');
    },

    render_list: function(orders){
        if (!!core.debug) {
            console.log('render_list order reservation', orders)
        }
        var contents = this.$el[0].querySelector('.order-list-contents');
        contents.innerHTML = "";
        for(var i = 0, len = Math.min(orders.length,1000); i < len; i++){
            var order = orders[i];

            // filter order based on tables
            var table_list = order.table_label;
            // if(posmodel.table.name == posmodel.table.name){
            if (table_list){
                if (table_list.includes(posmodel.table.name)){
                    var order_line_html = QWeb.render('PosOrderLine',{widget: this, order:order});
                    var order_line = document.createElement('tbody');
                    order_line.innerHTML = order_line_html;
                    order_line = order_line.childNodes[1];
                    contents.appendChild(order_line);
                }
            }

        }
    },

    perform_search: function(query, associate_result){
        var orders;
        if(query){
            orders = this.search_order(query);
            this.render_list(orders);
        }else{
            orders = this.pos.orderReservations;
            this.render_list(orders);
        }
    },
    clear_search: function(){
        var orders = this.pos.orderReservations;
        this.render_list(orders);
        this.$('.searchbox input')[0].value = '';
        this.$('.searchbox input').focus();
    },

    search_order: function(query){
        try {
            var re = RegExp(query, 'i');
        }catch(e){
            return [];
        }
        var results = [];
        for (var order_id in this.pos.orderReservations){
            var r = re.exec(this.pos.orderReservations[order_id]['name']+ '|'+ this.pos.orderReservations[order_id]['partner_id'][1]);
            if(r){
            results.push(this.pos.orderReservations[order_id]);
            }
        }
        return results;
    },

    line_select: function(event,$line,id){
        var self = this;
        var order = this.get_order_by_id(id);
        $line.addClass('highlight');
        this.gui.show_popup('order', {
            'order': order,
            'line':$line
        })
    },
    get_order_by_id:function(id){
        var orders = this.pos.orderReservations;
        var selected_order = [];
        var selected_lines = [];
        for (var i in orders){
            if (orders[i].id == id){

                for (var l in orders[i].lines){
                    selected_lines.push(orders[i].lines[l])
                }
                var order_lines = this.get_order_lines(selected_lines);
                selected_order.push({
                    'id': id,
                    'name': orders[i].name,
                    'partner':orders[i].partner_id[1],
                    'partner_id':orders[i].partner_id[0],
                    'session':orders[i].session_id[1],
                    'company':orders[i].company_id[1],
                    'amount_total': orders[i].amount_total,
                    // 'date_order': orders[i].date_order,
                    'date_order': orders[i].date_order_tz,
                    'start_time': orders[i].start_time_tz,
                    'end_time': orders[i].end_time_tz,
                    'pos_reference':orders[i].pos_reference,
                    'orderReservationLines':order_lines,
                    'state':orders[i].state,
                    'reserved_by':orders[i].reserved_by,
                    'booking_phone_number':orders[i].booking_phone_number,
                    'state_reservation':orders[i].state_reservation,
                    'table_label':orders[i].table_label,
                    'customer_count':orders[i].customer_count
                  })
            }
        }
        console.log('get_order_by_id', id, selected_order)
        return selected_order[0];
    },

    get_order_lines:function(lines){
        var selected_lines = [];
        var order_lines = this.pos.orderReservationLines;
        for (var l in order_lines){
            if (lines.indexOf(order_lines[l].id ) > -1){
                selected_lines.push({
                    'product': order_lines[l].product_id[1],
                    'product_id': order_lines[l].product_id[0],
                    'qty': order_lines[l].qty,
                    'discount': order_lines[l].discount,
                    'price_unit':  order_lines[l].price_unit,
                    'price_subtotal_incl':order_lines[l].price_subtotal_incl
                })
            }
        }
        return selected_lines;
    },
});

gui.define_screen({name:'order_list', widget: PosOrderScreenWidget});

var OrderListButton = screens.ActionButtonWidget.extend({
    template: 'OrderListButton',
    button_click: function(){
        var orders = this.pos.orderReservations;
        this.gui.show_screen('order_list',{orders:orders});
    }
});

screens.define_action_button({
    'name': 'pos_order_list',
    'widget': OrderListButton,
});

ClientListScreenWidget = ClientListScreenWidget.include({
    init: function(parent) {
        var self = this;
        this._super(parent);
        _.extend(self.events,
            {
            "click .view_orders":"view_customer_orders",
            })
    },
    view_customer_orders:function(e){
        e.stopPropagation();
        e.preventDefault();
        var partner = $(e.target).data('id');
        var orders = this.get_customer_orders(partner);
        this.gui.show_screen('order_list',{orders:orders});
    },
    get_customer_orders:function(partner){
        var customer_orders = [];
        var orders = this.pos.orderReservations;
        for (var i in orders){
            if(orders[i].partner_id[0]==partner){
                customer_orders.push(orders[i]);
            }
        }
        return customer_orders;
    },
});

screens.PaymentScreenWidget.include({

    // validate_order: function(force_validation) {
    finalize_validation: function() {
        var self = this;
        var order = this.pos.get_order()
        this._super()
        // console.log('order validated/paid, remove reservation from list!', order.reservation_order_id);
        if (!!order.reservation_order_id) {
            // remove selected reservation from existing list (already used/selected by user)
            this.pos.orderReservations = this.pos.orderReservations.filter(orderRes =>
                    orderRes.id != order.reservation_order_id);
            if (core.debug) {
                console.log('payment validated, order reservation now: ', this.pos.orderReservations);
            }
            // checkout ga usah dari sini, langsung dari python saat order ter process --> method: _process_order
//            rpc.query({
//                model: 'kg.pos.order.reservation',
//                method: 'set_check_out',
//                args: [null,order.reservation_order_id]
//             }).then(function (result) {
//                console.log('reservation check-out !', order.reservation_order_id);
//            });
        }
    },
});

models.PosModel = models.PosModel.extend({
    initialize: function(){
        PosModelSuper.prototype.initialize.apply(this, arguments);
        this.bus.add_channel_callback("pos_order_sync", this.on_order_create, this);
    },
    on_order_create: function(data){
        var self = this;
        var order_screen = self.gui.screen_instances.order_list;
        var fields = _.find(this.models,function(model){ return model.model === 'kg.pos.order.reservation'; }).fields;
        var line_fields = _.find(this.models,function(model){ return model.model === 'kg.pos.order.reservation'; }).fields;

        // TODO: fungsi ini belum berhasil jalan, perlu dicek lg
        console.log('on_order_create', data, self.orderReservations)

        // order_screen.pos.orderReservations[0].id
        // set order to checkout

        // custom code by andi
        if (!self.orderReservations.length) {
            return;
        }
        // end of custom code 

        // TODO: harusnya klo ada sinyal sync dari backend, data reservation jg di update

//        rpc.query({
//            model: 'kg.pos.order.reservation',
//            method: 'set_check_out',
//            args: [null,self.orderReservations[0].id]
//         }).then(function (result) {
//            console.log('reservation check-out !', self.orderReservations[0].id);
//        });

        rpc.query({
            model: 'kg.pos.order.reservation',
            method: 'search_read',
            args: [[['id', '=', data['order_id']]], fields],
            limit: 1,
        }).then(function (order){
            self.orderReservations.unshift(order[0]);
            _.each(data['lines'], function(line_id){
                rpc.query({
                    model: 'kg.pos.order.reservation.line',
                    method: 'search_read',
                    args: [[['id', '=', line_id]], line_fields],
                    limit: 1,
                }).then(function(line){
                    self.orderReservationLines.push(line[0]);
                });
            });
        });

    },

});

});

