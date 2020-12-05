odoo.define('kg_pos.department_expense', function(require) {
    'use_strict'

    var models = require('point_of_sale.models')
    var screens = require('point_of_sale.screens')
    var gui = require('point_of_sale.gui')
    var popups = require('point_of_sale.popups')
    var core = require('web.core')
    var field_utils = require('web.field_utils');

    var _t = core._t

    models.load_models({
        model: 'hr.department',
        field: [
            'name',
            'allow_pos_expense',
            'expense_account_id'
        ],
        loaded: function(self, departments) {
            self.department = departments
        }
    })

    var _super_order = models.Order.prototype
    models.Order = models.Order.extend({
        initialize: function() {
            _super_order.initialize.apply(this, arguments)

            this.department_id = this.department_id
            this.journal_id = this.journal_id
            
            this.save_to_db()
        },
        export_as_JSON: function() {
            var json = _super_order.export_as_JSON.apply(this, arguments)
            // json.meal_type = this.meal_type ? this.meal_type.name : undefined
            json.department_id = this.department_id
            json.journal_id = this.journal_id
            return json
        },
        init_from_JSON: function(json) {
            _super_order.init_from_JSON.apply(this, arguments)

            this.department_id = json.department_id
            this.journal_id = json.journal_id
        },
        export_for_printing: function() {
            var json = _super_order.export_for_printing.apply(this, arguments)
            json.department_id = this.department_id
            json.journal_id = this.journal_id
            return json
        },
        set_department: function(department_id) {
            this.department_id = department_id
            this.trigger('change')
        },
        get_department: function() {
            var department_id = this.department_id
            return {
                department_id
            }
        },

        // add_paymentline: function(cashregister) {
        //     this.assert_editable();
        //     var newPaymentline = new models.Paymentline({},{order: this, cashregister:cashregister, pos: this.pos});
        //     if (cashregister.journal.is_department_expense){
        //         newPaymentline.set_amount( this.get_due() );
        //     }

        //     if (cashregister.journal.type !== 'cash' || this.pos.config.iface_precompute_cash){
        //         newPaymentline.set_amount( this.get_due() );
        //     }

        //     this.paymentlines.add(newPaymentline);
        //     this.select_paymentline(newPaymentline);

        // },

        // get_new_total: function() {
        //     if (_.values(this.pos.get_order().paymentlines._byId)[0].cashregister.journal.is_department_expense) {
        //         return this.get_total_without_tax()
        //     }
        //     else {
        //         return this.get_total_with_tax()
        //     }

        // },
    })

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function() {
            _super_orderline.initialize.apply(this, arguments)
        },
        export_as_JSON: function() {
            var json = _super_orderline.export_as_JSON.apply(this, arguments)
            return json
        },
        init_from_JSON: function(json) {
            _super_orderline.init_from_JSON.apply(this, arguments)
        },
        export_for_printing: function() {
            var json = _super_orderline.export_for_printing.apply(this, arguments)
            return json
        },

        // get_tax_details: function(){
        //     if (_.values(this.pos.get_order().paymentlines._byId)[0].cashregister.journal.is_department_expense) {
        //         return 0
        //     }
        //     else {
        //         return this.get_all_prices().taxDetails;
        //     }

        // },

    })

    var _super_paymentline = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
        initialize: function() {
            _super_paymentline.initialize.apply(this, arguments)
        },
        export_as_JSON: function() {
            var json = _super_paymentline.export_as_JSON.apply(this, arguments)
            return json
        },
        init_from_JSON: function(json) {
            _super_paymentline.init_from_JSON.apply(this, arguments)
        },
        export_for_printing: function() {
            var json = _super_paymentline.export_for_printing.apply(this, arguments)
            return json
        },

        // get_new_amount: function(){
        //     if (this.cashregister.journal.is_department_expense) {
        //         if (this.pos.get_order() !== null) {
        //             return this.pos.get_order().get_total_without_tax()
        //         }
        //         else {
        //             return this.amount;
        //         }
        //     }
        //     else {
        //         return this.amount;
        //     }

        // },

    })


    // screens.PaymentScreenWidget.include({
    //     click_paymentmethods: function(id) {
    //         var depexpaymentbyId = []
    //         var paymentlines = _.values(this.pos.get_order().paymentlines._byId)
    //         for (var i = 0; i < this.pos.cashregisters.length; i++) {
    //             if (this.pos.cashregisters[i].journal.is_department_expense){
    //                 depexpaymentbyId.push(
    //                     this.pos.cashregisters[i].journal.id
    //                 );
    //             }
    //         }
    //         if (paymentlines[0]){
    //             if (depexpaymentbyId.includes(paymentlines[0].cashregister.journal.id) === false) {
    //                 if (depexpaymentbyId.includes(id)){
    //                     this.gui.show_popup('error',{
    //                         title: _t('Payment Method Restriction'),
    //                         body:  _t('You cannot choose this payment method'),
    //                     });
    //                 }
    //                 else{
    //                     var cashregister = null;
    //                     for ( var i = 0; i < this.pos.cashregisters.length; i++ ) {
    //                         if ( this.pos.cashregisters[i].journal_id[0] === id ){
    //                             cashregister = this.pos.cashregisters[i];
    //                             break;
    //                         }
    //                     }
    //                     this.pos.get_order().add_paymentline( cashregister );
    //                     this.reset_input();
    //                     this.render_paymentlines();
    //                 }
    //             }
    //             else if (depexpaymentbyId.includes(paymentlines[0].cashregister.journal.id)) {
    //                 if (depexpaymentbyId.includes(id)) {
    //                     if (paymentlines[0].cashregister.journal.id !== id) {
    //                         this.gui.show_popup('error',{
    //                             title: _t('Payment Method Restriction'),
    //                             body:  _t('You cannot choose this payment method'),
    //                         });
    //                     }
    //                 }
    //                 else if (!depexpaymentbyId.includes(id)){
    //                     this.gui.show_popup('error',{
    //                         title: _t('Payment Method Restriction'),
    //                         body:  _t('You cannot choose this payment method'),
    //                     });
    //                 }
    //             }
    //         }
    //         else {
    //             var cashregister = null;
    //             for ( var i = 0; i < this.pos.cashregisters.length; i++ ) {
    //                 if ( this.pos.cashregisters[i].journal_id[0] === id ){
    //                     cashregister = this.pos.cashregisters[i];
    //                     break;
    //                 }
    //             }
    //             if (cashregister.journal.is_department_expense){
    //                 var self = this
    //                 var list = [];
    //                 for (var i = 0; i < this.pos.department.length; i++) {
    //                     var department = this.pos.department[i];
    //                     if (department.allow_pos_expense) {
    //                         list.push({
    //                             'label': department.name,
    //                             'item':  department,
    //                         });
    //                     }
    //                 }

    //                 self.gui.show_popup('selection',{
    //                     title: _t('Choose Department'),
    //                     list: list,
    //                     confirm: function(item){
    //                         var department_id = item

    //                         self.pos
    //                             .get_order()
    //                             .set_department(department_id)

    //                         self.pos.get_order().add_paymentline( cashregister );
    //                         self.reset_input();
    //                         self.render_paymentlines();

    //                     },
    //                     is_selected: function (department_id) {
    //                         return department_id.id === self.pos.get_order().get_department().department_id.id;
    //                     },
    //                 });

    //             }

    //             else {
    //                 this.pos.get_order().add_paymentline( cashregister );
    //                 this.reset_input();
    //                 this.render_paymentlines();
    //             }
    //         }

    //     },
    //     // payment_input: function(input) {
    //     //     var paymentlist = _.values(this.pos.get_order().paymentlines._byId)
    //     //     var has_dept_expense = false
    //     //     for (var i = 0; i < paymentlist.length; i++) {
    //     //         if (paymentlist[i].cashregister.journal.is_department_expense) {
    //     //             has_dept_expense = true;
    //     //             break;
    //     //         }
    //     //
    //     //     if (!has_dept_expense) {
    //     //         this._super(input)
    //     //     }
    //     //
    //     //     }
    //     // },
    // })
})
