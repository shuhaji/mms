odoo.define('kg_base.city_ledger', function(require) {
    'use_strict'

    var models = require('point_of_sale.models')
    var screens = require('point_of_sale.screens')
    var gui = require('point_of_sale.gui')
    var popups = require('point_of_sale.popups')
    var core = require('web.core')
    var field_utils = require('web.field_utils');

    var _t = core._t

    // models.load_models({
    //     model:  'res.partner',
    //     fields: [
    //         'name',
    //         'street',
    //         'city',
    //         'state_id',
    //         'country_id',
    //         'vat',
    //         'phone',
    //         'zip',
    //         'mobile',
    //         'email',
    //         'barcode',
    //         'write_date',
    //         'property_account_position_id',
    //         'property_product_pricelist',
    //         'allow_use_city_ledger',
    //         'expense_account_id'],
    //     domain: [['customer','=',true]],
    //     loaded: function(self,partners){
    //         self.partners = partners;
    //         self.db.add_partners(partners);
    //     },
    // })

    // models.load_models({
    //     model:  'account.journal',
    //     fields: [
    //         'type',
    //         'sequence',
    //         'is_department_expense',
    //         'is_officer_check',
    //         'is_city_ledger',
    //     ],
    //     domain: function(self,tmp){ return [['id','in',tmp.journals]]; },
    //     loaded: function(self, journals){
    //         var i;
    //         self.journals = journals;

    //         // associate the bank statements with their journals.
    //         var cashregisters = self.cashregisters;
    //         var ilen = cashregisters.length;
    //         for(i = 0; i < ilen; i++){
    //             for(var j = 0, jlen = journals.length; j < jlen; j++){
    //                 if(cashregisters[i].journal_id[0] === journals[j].id){
    //                     cashregisters[i].journal = journals[j];
    //                 }
    //             }
    //         }

    //         self.cashregisters_by_id = {};
    //         for (i = 0; i < self.cashregisters.length; i++) {
    //             self.cashregisters_by_id[self.cashregisters[i].id] = self.cashregisters[i];
    //         }

    //         self.cashregisters = self.cashregisters.sort(function(a,b){
    //             // prefer cashregisters to be first in the list
    //             if (a.journal.type == "cash" && b.journal.type != "cash") {
    //                 return -1;
    //             } else if (a.journal.type != "cash" && b.journal.type == "cash") {
    //                 return 1;
    //             } else {
    //                 return a.journal.sequence - b.journal.sequence;
    //             }
    //         });
    //     }
    // })

    var _super_order = models.Order.prototype
    models.Order = models.Order.extend({
        initialize: function() {
            _super_order.initialize.apply(this, arguments)

            this.customer_id = this.customer_id
            this.change = this.get_change()

            this.save_to_db()
        },
        export_as_JSON: function() {
            var json = _super_order.export_as_JSON.apply(this, arguments)
            // json.meal_type = this.meal_type ? this.meal_type.name : undefined
            json.customer_id = this.customer_id
            json.change = this.get_change()

            return json
        },
        init_from_JSON: function(json) {
            _super_order.init_from_JSON.apply(this, arguments)

            this.customer_id = json.customer_id
            this.change = this.get_change()

        },
        export_for_printing: function() {
            var json = _super_order.export_for_printing.apply(this, arguments)
            json.customer_id = this.customer_id
            json.change = this.get_change()
            return json
        },
        set_customer: function(customer_id) {
            this.customer_id = customer_id
            this.trigger('change')
        },
        get_customer: function() {
            var customer_id = this.customer_id
            return {
                customer_id
            }
        },

        // add_paymentline: function(cashregister) {
        //     this.assert_editable();
        //     var newPaymentline = new models.Paymentline({},{order: this, cashregister:cashregister, pos: this.pos});
        //     if (cashregister.journal.is_officer_check){
        //         newPaymentline.set_amount( this.get_due() );
        //     }

        //     if (cashregister.journal.is_department_expense){
        //         newPaymentline.set_amount( this.get_due() );
        //     }

        //     if (cashregister.journal.is_city_ledger){
        //         newPaymentline.set_amount( this.get_due() );
        //     }

        //     if (cashregister.journal.type !== 'cash' || this.pos.config.iface_precompute_cash){
        //         newPaymentline.set_amount( this.get_due() );
        //     }

        //     this.paymentlines.add(newPaymentline);
        //     this.select_paymentline(newPaymentline);
        // },

        // get_new_total: function() {
        //     if (_.values(this.pos.get_order().paymentlines._byId)[0].cashregister.journal.is_officer_check) {
        //         return this.get_total_without_tax()
        //     }
        //     else if (_.values(this.pos.get_order().paymentlines._byId)[0].cashregister.journal.is_department_expense) {
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
        //     if (_.values(this.pos.get_order().paymentlines._byId)[0].cashregister.journal.is_officer_check) {
        //         return 0
        //     }
        //     else if (_.values(this.pos.get_order().paymentlines._byId)[0].cashregister.journal.is_department_expense) {
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
        //     if (this.cashregister.journal.is_officer_check) {
        //         if (this.pos.get_order() !== null) {
        //             return this.pos.get_order().get_total_without_tax()
        //         }
        //         else {
        //             return this.amount;
        //         }
        //     }
        //     else if (this.cashregister.journal.is_department_expense) {
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
    //         var officercheckpaymentbyId = []
    //         var depexpaymentbyId = []
    //         var cityledgerbyId = []
    //         var paymentlines = _.values(this.pos.get_order().paymentlines._byId)

    //         for (var i = 0; i < this.pos.cashregisters.length; i++) {
    //             if (this.pos.cashregisters[i].journal.is_officer_check){
    //                 officercheckpaymentbyId.push(
    //                     this.pos.cashregisters[i].journal.id
    //                 );
    //             }
    //         }

    //         for (var i = 0; i < this.pos.cashregisters.length; i++) {
    //             if (this.pos.cashregisters[i].journal.is_department_expense){
    //                 depexpaymentbyId.push(
    //                     this.pos.cashregisters[i].journal.id
    //                 );
    //             }
    //         }

    //         for (var i = 0; i < this.pos.cashregisters.length; i++) {
    //             if (this.pos.cashregisters[i].journal.is_city_ledger){
    //                 cityledgerbyId.push(
    //                     this.pos.cashregisters[i].journal.id
    //                 );
    //             }
    //         }

    //         if (paymentlines[0]){
    //             if ((officercheckpaymentbyId.includes(paymentlines[0].cashregister.journal.id) || depexpaymentbyId.includes(paymentlines[0].cashregister.journal.id) || cityledgerbyId.includes(paymentlines[0].cashregister.journal.id)) === false) {
    //                 if (officercheckpaymentbyId.includes(id) || depexpaymentbyId.includes(id) || cityledgerbyId.includes(id)){
    //                     this.gui.show_popup('error',{
    //                         title: _t('Payment Method Restriction'),
    //                         body:  _t('You cannot choose this payment method'),
    //                     });
    //                 }

    //                 // else if (depexpaymentbyId.includes(id)){
    //                 //     this.gui.show_popup('error',{
    //                 //         title: _t('Payment Method Restriction'),
    //                 //         body:  _t('You cannot choose this payment method'),
    //                 //     });
    //                 // }

    //                 else {
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
    //             else if (officercheckpaymentbyId.includes(paymentlines[0].cashregister.journal.id) || depexpaymentbyId.includes(paymentlines[0].cashregister.journal.id) || cityledgerbyId.includes(paymentlines[0].cashregister.journal.id)) {
    //                 if (officercheckpaymentbyId.includes(id)){
    //                     if (paymentlines[0].cashregister.journal.id !== id) {
    //                         this.gui.show_popup('error',{
    //                             title: _t('Payment Method Restriction'),
    //                             body:  _t('You cannot choose this payment method'),
    //                         });
    //                     }
    //                 }

    //                 else if (depexpaymentbyId.includes(id)) {
    //                     if (paymentlines[0].cashregister.journal.id !== id) {
    //                         this.gui.show_popup('error',{
    //                             title: _t('Payment Method Restriction'),
    //                             body:  _t('You cannot choose this payment method'),
    //                         });
    //                     }
    //                 }

    //                 else if (cityledgerbyId.includes(id)) {
    //                     if (paymentlines[0].cashregister.journal.id !== id) {
    //                         this.gui.show_popup('error',{
    //                             title: _t('Payment Method Restriction'),
    //                             body:  _t('You cannot choose this payment method'),
    //                         });
    //                     }
    //                 }

    //                 else if (!officercheckpaymentbyId.includes(id)) {
    //                     this.gui.show_popup('error',{
    //                         title: _t('Payment Method Restriction'),
    //                         body:  _t('You cannot choose this payment method'),
    //                     });
    //                 }

    //                 else if (!depexpaymentbyId.includes(id)) {
    //                     this.gui.show_popup('error',{
    //                         title: _t('Payment Method Restriction'),
    //                         body:  _t('You cannot choose this payment method'),
    //                     });
    //                 }

    //                 else if (!cityledgerbyId.includes(id)) {
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
    //             if (cashregister.journal.is_officer_check){
    //                 var self = this
    //                 var list = [];
    //                 for (var i = 0; i < this.pos.employee.length; i++) {
    //                     var employee = this.pos.employee[i];
    //                     if (employee.is_officer_check) {
    //                         list.push({
    //                             'label': employee.name,
    //                             'item':  employee,
    //                         });
    //                     }
    //                 }

    //                 self.gui.show_popup('selection',{
    //                     title: _t('Choose Department'),
    //                     list: list,
    //                     confirm: function(item){
    //                         var employee_id = item

    //                         self.pos
    //                             .get_order()
    //                             .set_employee(employee_id)

    //                         self.pos.get_order().add_paymentline( cashregister );
    //                         self.reset_input();
    //                         self.render_paymentlines();

    //                     },
    //                     is_selected: function (employee_id) {
    //                         return employee_id.id === self.pos.get_order().get_employee().employee_id.id;
    //                     },
    //                 });

    //             }

    //             else if (cashregister.journal.is_department_expense){
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

    //             else if (cashregister.journal.is_city_ledger){
    //                 var self = this
    //                 var list = [];
    //                 for (var i = 0; i < this.pos.partners.length; i++) {
    //                     var partner = this.pos.partners[i];
    //                     if (partner.allow_use_city_ledger) {
    //                         list.push({
    //                             'label': partner.name,
    //                             'item':  partner,
    //                         });
    //                     }
    //                 }
    //                 self.gui.show_popup('selection',{
    //                     title: _t('Choose Customer'),
    //                     list: list,
    //                     confirm: function(item){
    //                         var customer_id = item
    //                         self.pos
    //                             .get_order()
    //                             .set_customer(customer_id)

    //                         self.pos.get_order().add_paymentline( cashregister );
    //                         self.reset_input();
    //                         self.render_paymentlines();

    //                     },
    //                     is_selected: function (customer_id) {
    //                         return customer_id.id === self.pos.get_order().get_customer().customer_id.id;
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

    //     payment_input: function(input) {
    //         var paymentlist = _.values(this.pos.get_order().paymentlines._byId)
    //         var has_employee_expense = false
    //         var has_dept_expense = false
    //         var has_city_ledger_expense = false
    //         for (var i = 0; i < paymentlist.length; i++) {
    //             if (paymentlist[i].cashregister.journal.is_officer_check) {
    //                 has_employee_expense = true;
    //                 break;
    //             }

    //             if (paymentlist[i].cashregister.journal.is_department_expense) {
    //                 has_dept_expense = true;
    //                 break;
    //             }

    //             if (paymentlist[i].cashregister.journal.is_city_ledger) {
    //                 has_city_ledger_expense = true;
    //                 break;
    //             }
    //         }

    //         if (!(has_employee_expense || has_dept_expense || has_city_ledger_expense)) {
    //             this._super(input)
    //         }
    //         // if (!has_dept_expense) {
    //         //     this._super(input)
    //         // }
    //     },
    // })

})
