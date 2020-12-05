odoo.define('kg_account.credit_card', function(require) {
    'use_strict'

    var models = require('point_of_sale.models')
    var screens = require('point_of_sale.screens')
    var gui = require('point_of_sale.gui')
    var popups = require('point_of_sale.popups')
    var core = require('web.core')
    var field_utils = require('web.field_utils')
    var BarcodeEvents = require('barcodes.BarcodeEvents').BarcodeEvents

    var _t = core._t

    var CreditCardPopup = popups.extend({
        template: 'CreditCardPopup',
        show: function(options) {
            var self = this
            options = options || {}
            this._super(options)

            var order = self.pos.get_order()

            // this.issuer_bank = order.issuer_bank ? parseInt(order.issuer_bank) : null;
            this.issuer_type = parseInt(order.issuer_type)
            this.card_holder_name = order.card_holder_name
            this.front_card_number = order.front_card_number
            this.back_card_number = order.back_card_number
            this.enable_keypress = true

            this.renderElement()
            // var issuer_banks = this.pos.issuer_banks
            // var issuer_types = this.pos.issuer_types
            var self = this
//            var selectedBank = this.$('#issuer-bank')
//            selectedBank.change(function(event) {
//                self.selected_bank(event, issuer_banks, issuer_types)
//            })
            this.$('#front-card-number').on('input', this.check_length)
            this.$('#back-card-number').on('input', this.check_length)

            // this.$('#issuer-bank').on('change', this.selected_bank(event,issuer_banks, issuer_types))
        },

        click_confirm: function(event) {
            var self = this
            // var issuerBank = this.$('#issuer-bank').val()
            var issuerType = this.$('#issuer-type').val()
            var cardHoldername = this.$('#card-holder-name').val()
            var frontCardnumber = this.$('#front-card-number').val()
            var backCardnumber = this.$('#back-card-number').val()
            var cashregister = this.pos.get_order().selected_cashregister

            var order = this.pos.get_order()
            order.set_allow_press_payment_numpad(true)

            if (!(issuerType && cardHoldername && frontCardnumber && backCardnumber)) {
                this.gui.show_popup('error', {
                    title: _t('Invalid Value'),
                    body: _t(
                        'You must fill all the field required'
                    ),
                })
            }
            else if (issuerType && cardHoldername && frontCardnumber && backCardnumber) {

                this.gui.close_popup()
                issuerType = parseInt(issuerType)
                order.add_paymentline(cashregister)
                var newPaymentLine = order.selected_paymentline
                newPaymentLine.issuer_type = issuerType
                newPaymentLine.card_holder_name = cardHoldername
                newPaymentLine.front_card_number = frontCardnumber
                newPaymentLine.back_card_number = backCardnumber
                issuer_type_model = self.pos.issuer_types.find(type => type.id === issuerType)
                newPaymentLine.issuer_type_name = issuer_type_model.name

                this.pos.payment_widget.reset_input()
                this.pos.payment_widget.render_paymentlines()
            }
        },

        check_length: function(event) {
            const el = event.target
            if (el.value.length > el.max.length) {
                el.value = el.value.slice(0, el.max.length)
            }
        },

        selected_bank: function(event, issuer_banks, issuer_types) {
//            var list_of_banks = issuer_banks
//            var list_of_types = issuer_types
//            var selected_bank = parseInt(event.target.value)
//            var current_types = ['<option></option>']
//            for (var i = 0; i < issuer_types.length; i++) {
//                if (issuer_types[i].journal_bank_id[0] === selected_bank) {
//                    current_types.push(
//                        `<option value=${issuer_types[i].id}>` +
//                            issuer_types[i].name +
//                            '</option>'
//                    )
//                }
//            }
//            $('#issuer-type')
//                .empty()
//                .append(current_types)
        },
    })
    gui.define_popup({ name: 'credit-card', widget: CreditCardPopup })
})
