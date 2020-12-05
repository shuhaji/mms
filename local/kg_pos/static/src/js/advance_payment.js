odoo.define('kg_pos.advance_payment', function(require) {
    'use_strict'

    var models = require('point_of_sale.models')
    var screens = require('point_of_sale.screens')
    var gui = require('point_of_sale.gui')
    var popups = require('point_of_sale.popups')
    var core = require('web.core')
    var session = require('web.session')
    // var numeral = require('numeral');

    var _t = core._t
    var utils = require('web.utils');
    var round_pr = utils.round_precision;

    models.load_models({
        model: 'account.invoice',
        field: [
            'name',
            'invoice_collecting_id',
            'origin',
            'number',
            'state',
            'reference_type',
            'reference',
            'partner_id',
            'account_id',
            'currency_id',
            'journal_id',
            'company_id',
            'date_invoice',
            'date_due',
            'invoice_line_ids',
            'tax_line_ids',
            'amount_untaxed',
            'amount_total',
            'residual',
        ],
        loaded: function(self, invoices) {
            self.invoice = invoices
        }
    })
    
    models.load_models({
        model: 'account.payment',
        field: [
            'name',
            'partner_id',
            'company_id',
            'amount',
            'residual',
            'residual_temp',
            'journal_id', 
            'deposit_type_id',
            'payment_date',
            'validate_date',
            'is_advance_payment',
            'advance_payment_account_id',
        ],
        domain: ['&', '&', 
            ['is_advance_payment','=',true],
            ['state', '=', 'posted'],
            ['residual_temp', '>', 0]
        ],
        loaded: function(self, payment) {
            self.payment = []
            for (var i = 0; i < payment.length; i++) {
                if (payment[i].company_id[0] === self.user.company_id[0]) {
                    if (payment[i].deposit_type_id === false || payment[i].deposit_type_id[1] === 'POS') {
                        if (['NEW', 'CONFIRMED'].includes(payment[i].status_deposit)) {
                            self.payment.push(payment[i])
                        }
                    }
                }
            }
            self.duplicated_payment = payment
        }
    })

    models.load_models({
        model:  'res.partner',
        fields: [
            'name',
            'street',
            'city',
            'state_id',
            'country_id',
            'vat',
            'phone',
            'zip',
            'mobile',
            'email',
            'barcode',
            'write_date',
            'property_account_position_id',
            'property_product_pricelist',
            'allow_use_city_ledger'],
        domain: [['customer','=',true]],
        loaded: function(self,partners){
            self.partners = partners;
            self.db.add_partners(partners);

            var valid_adv_payment_partner_by_id = self.payment.map(pay => pay.partner_id).map(partner => partner[0])
            var valid_adv_payment_partner = []

            for (var i = 0; i < self.partners.length; i++) {
                if (valid_adv_payment_partner_by_id.includes(partners[i].id)){
                    valid_adv_payment_partner.push(
                        partners[i]
                    )
                }
            }
            self.valid_adv_payment_partner = valid_adv_payment_partner
            // console.log('partner', valid_adv_payment_partner)
        },
    })
    
    // models.load_models({
    //     model:  'res.partner',
    //     loaded: function(self,partners){
    //         var valid_adv_payment_partner_by_id = self.payment.map(pay => pay.partner_id).map(partner => partner[0])
    //         var valid_adv_payment_partner = []

    //         for (var i = 0; i < self.partners.length; i++) {
    //             if (valid_adv_payment_partner_by_id.includes(partners[i].id)){
    //                 valid_adv_payment_partner.push(
    //                     partners[i]
    //                 )
    //             }
    //         }
    //         self.valid_adv_payment_partner = valid_adv_payment_partner
    //     },
    // })

    var _super_order = models.Order.prototype
    models.Order = models.Order.extend({
        initialize: function() {
            _super_order.initialize.apply(this, arguments)

            this.invoice = this.invoice
            this.adv_payment = this.adv_payment
            this.adv_payment_partner = this.adv_payment_partner
            this.adv_payment_account = this.adv_payment_account
            this.adv_payment_amount = this.adv_payment_amount
            this.adv_payment_residual = this.adv_payment_residual
            this.adv_payment_deposit = this.adv_paymentdeposit 
            this.adv_payment_model = this.adv_payment_model
            this.adv_payment_partner_model = this.adv_payment_partner_model
            this.adv_payment_new_payment_amount = this.adv_payment_new_payment_amount

            this.save_to_db()
        },
        export_as_JSON: function() {
            var json = _super_order.export_as_JSON.apply(this, arguments)
            // json.meal_time = this.meal_time ? this.meal_time.name : undefined
            json.invoice = this.invoice
            json.invoice = this.invoice
            json.adv_payment = this.adv_payment
            json.adv_payment_partner = this.adv_payment_partner
            json.adv_payment_account = this.adv_payment_account
            json.adv_payment_amount = this.adv_payment_amount
            json.adv_payment_residual = this.adv_payment_residual
            json.adv_payment_deposit = this.adv_payment_deposit
            json.adv_payment_model = this.adv_payment_model
            json.adv_payment_partner_model = this.adv_payment_partner_model
            json.adv_payment_new_payment_amount = this.adv_payment_new_payment_amount

            return json
        },
        init_from_JSON: function(json) {
            _super_order.init_from_JSON.apply(this, arguments)

            this.invoice = json.invoice
            this.adv_payment = json.adv_payment
            this.adv_payment_partner = json.adv_payment_partner
            this.adv_payment_account = json.adv_payment_account
            this.adv_payment_amount = json.adv_payment_amount
            this.adv_payment_residual = json.adv_payment_residual
            this.adv_payment_deposit = json.adv_payment_deposit
            this.adv_payment_model = json.adv_payment_model
            this.adv_payment_partner_model = json.adv_payment_partner_model
            this.adv_payment_new_payment_amount = json.adv_payment_new_payment_amount

        },
        export_for_printing: function() {
            var json = _super_order.export_for_printing.apply(this, arguments)

            json.invoice = this.invoice
            json.adv_payment = this.adv_payment
            json.adv_payment_partner = this.adv_payment_partner
            json.adv_payment_account = this.adv_payment_account
            json.adv_payment_amount = this.adv_payment_amount
            json.adv_payment_residual = this.adv_payment_residual
            json.adv_payment_deposit = this.adv_payment_deposit
            json.adv_payment_model = this.adv_payment_model
            json.adv_payment_partner_model = this.adv_payment_partner_model
            json.adv_payment_new_payment_amount = this.adv_payment_new_payment_amount

            return json
        },
        set_payment: function(adv_payment, partner, account,
            originalDepositAmount, residual, depositTypeId, newPaymentAmount) {
            this.adv_payment = adv_payment
            this.adv_payment_partner = partner
            this.adv_payment_account = account
            this.adv_payment_amount = originalDepositAmount
            this.adv_payment_residual = residual
            this.adv_payment_deposit = depositTypeId
            this.adv_payment_model = this.pos.payment.find(payment => payment.id === this.adv_payment)
            this.adv_payment_partner_model = this.pos.partners.find(partner => partner.id === this.adv_payment_partner)
            this.adv_payment_new_payment_amount = newPaymentAmount
            
            this.trigger('change')
        },
        get_payment: function() {
            return {
                adv_payment: this.adv_payment,
                adv_payment_partner: this.adv_payment_partner,
                adv_payment_account: this.adv_payment_account,
                adv_payment_amount: this.adv_payment_amount,
                adv_payment_residual: this.adv_payment_residual,
                adv_payment_deposit: this.adv_payment_deposit,
            }
        },
    })

    var AdvancePaymentPopup = popups.extend({
        template: 'AdvancePaymentPopup',
        show: function(options) {
            var self = this
            var order = this.pos.get_order()
            options = options || {}
            this._super(options)
            
            this.invoice = order.invoice
            this.payment = order.payment
            
            this.renderElement()
            
            var list_payment = this.pos.payment
            var partner = this.pos.partners
            var self_order = this
            var used_adv_payment_by_id = []
            var zero_residual_adv_payment_id = []

            console.log('adv deposit', list_payment)
            // get list of payment that already used in current order
            if (order.used_adv_payment) {
                if (order.used_adv_payment[0]) {
                    for (var i = 0; i < order.used_adv_payment.length; i++) {

                        if (order.used_adv_payment[i].full_used_adv_payment) {
                            used_adv_payment_by_id.push(
                                order.used_adv_payment[i].current_adv_payment.id
                            )
                        }
                    }
                }
            }
            // filter out payment that already used
            // get only unused adv payment and residual_temp > 0
            if (used_adv_payment_by_id.length > 0) {
                list_payment = list_payment.filter(pay =>
                    (!used_adv_payment_by_id.includes(pay.id) && pay.residual_temp > 0))
            }
            console.log('list payment 2', list_payment)
            // end of code
            console.log('order list adv payment', order.list_of_adv_payments, used_adv_payment_by_id)
            if (!order.list_of_adv_payments || order.list_of_adv_payments.length < 1) {
                order.list_of_adv_payments = list_payment
            } else {
                // get only unused adv payment and residual_temp > 0
                order.list_of_adv_payments = order.list_of_adv_payments.filter(pay =>
                    (!used_adv_payment_by_id.includes(pay.id) && pay.residual_temp > 0))
            }
            var payment = order.list_of_adv_payments
            console.log('order list adv payment 2', payment)
            if (order.adv_payment_partner){
                var current_payment = ['<option></option>']
                for (var i = 0; i < payment.length; i++) {
                    if (payment[i].partner_id[0] === order.adv_payment_partner) {
                        current_payment.push(
                            `<option value=${payment[i].id}>` +
                            payment[i].name +
                            '</option>'
                        )
                    }
                }
                $('#payment').empty().append(current_payment)
            }

            selectedPartner = this.$('#partner')
            selectedPayment = this.$('#payment')
            

            selectedPartner.change(function(event) {
                self.selected_partner(event, list_payment, payment, partner, self_order)
            })

            selectedPayment.change(function(event) {
                self.selected_payment(event, list_payment, payment, partner, self_order)
            })
        },

        selected_partner: function(event, list_payment, payment, partner, self_order) {
            var selected_partner = parseInt(event.target.value)
            var current_partner = false
            var current_payment = ['<option></option>']
            var order = self_order.pos.get_order()
            var advance_payment_line = false
            if (order) {
                advance_payment_line = order.get_paymentlines().filter(payment => payment.cashregister.journal.is_advance_payment)[0]
            }

            if (advance_payment_line) {
                if (order.adv_payment_partner) {
                    this.gui.show_popup('error', {
                        title: _t('Change Partner Restriction'),
                        body: _t(
                            'You already set a partner for this advance payment'
                        ),
                    })
                }
            }
            
            for (var i = 0; i < partner.length; i++) {
                if (partner[i].id === parseInt(selected_partner)) {
                    current_partner = partner[i]
                }
            }

            for (var i = 0; i < payment.length; i++) {
                if (payment[i].partner_id[0] === parseInt(selected_partner)) {
                    current_payment.push(
                        `<option value=${payment[i].id}>` +
                        payment[i].name +
                        '</option>'
                    )
                }
            }

            var deposit = '<option></option>'

            $('#payment').empty().append(current_payment)
            $('#deposit').empty().append(deposit)
            $('#amount').val(null)
            $('#residual').val(null)
            $('#payment-amount').val(null)

        },
        selected_payment: function(event, list_payment, payment, partner, self_order){
            var selected_payment = parseInt(event.target.value)
            var current_partner = false
            var current_payment = false
            this.enable_keypress = true

            for (var i = 0; i < list_payment.length; i++) {
                if (list_payment[i].id === parseInt(selected_payment)) {
                    current_payment = list_payment[i]
                }
            }

            var deposit = '<option></option>'

            if (current_payment) {
                if (current_payment.deposit_type_id){
                    var deposit = `<option value=${current_payment.deposit_type_id[0]}>` +
                    current_payment.deposit_type_id[1] +
                    '</option>'
                }
                
                $('#deposit').empty().append(deposit)
                // original deposit amount
                // $('#amount').val(numeral(current_payment.amount).format('0,0.00'))
                // $('#residual').val(numeral(current_payment.residual_temp).format('0,0.00'))
                $('#amount').val(this.numberWithCommas(current_payment.amount))
                $('#residual').val(this.numberWithCommas(current_payment.residual_temp))

                var amount_due = this.pos.get_order().get_due()
                var currency_rounding = this.pos.currency.rounding

                var new_amount_payment = (amount_due < current_payment.residual_temp) ? amount_due : current_payment.residual_temp
                // utk menghilangkan kasus angka: 5.8100000000000005 (ga mau bulat2)
                new_amount_payment = this.stringToFloat(this.numberWithCommas(new_amount_payment))
                $('#order-remaining-amount').html(this.format_currency(amount_due))
                $('#payment-amount').attr({
                   "max" : new_amount_payment, // maksimum payment
                   "min" : 1
                });
                $('#payment-amount').val(new_amount_payment)
            }
        },
        numberWithCommas:function (number) {
            return number.toLocaleString("en")
        },
        stringToFloat: function(value) {
            // dari 123,567,323.00 jadi: 123567323.00
            return parseFloat(value.replace(/\,/g,'')) || 0.0
        },
    })
    gui.define_popup({ name: 'advance-payment', widget: AdvancePaymentPopup })


})
