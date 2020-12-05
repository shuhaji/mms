odoo.define('kg_pos.voucher_payment', function(require) {
    'use_strict'

    var models = require('point_of_sale.models')
    var screens = require('point_of_sale.screens')
    var gui = require('point_of_sale.gui')
    var popups = require('point_of_sale.popups')
    var core = require('web.core')
    var field_utils = require('web.field_utils')
    var BarcodeEvents = require('barcodes.BarcodeEvents').BarcodeEvents

    var _t = core._t

    // load data kg.voucher, taruh ke pos .. lihat contoh di issuer_type
    models.load_models({
        model: 'kg.voucher',
        fields: ['name', 'is_open_amount', 'is_external', 'amount'],
        // TODO: test, check apakah filter date ini jalan dg benar?
        domain: function(self) {return [
            ['company_id', '=', self.company && self.company.id || false]
            , ['active', '=', true]
            , ['start_date', '<=', (new Date()).toISOString()]
            , ['end_date', '>=', (new Date()).toISOString()]
        ]},
        loaded: function(self, kg_vouchers) {
            // console.log('user company: ', self.user.company_id[0], 'self.company: ', self.company)
            self.kg_vouchers = kg_vouchers
        },
    });

    var VoucherPopup = popups.extend({
        template: 'VoucherPopup',
        show: function(options) {
            var self = this
            options = options || {}
            this._super(options)

            var order = self.pos.get_order()

            this.enable_keypress = true

            this.renderElement()

//            this.$('#front-card-number').on('input', this.check_length)
//            this.$('#back-card-number').on('input', this.check_length)

            self.$('#voucher-payment').change(function(event) {
                self.select_voucher(event)
            })
        },

        click_confirm: function(event) {
            // var issuerBank = this.$('#issuer-bank').val()
            var self = this
            var voucher_id = parseInt(self.$('#voucher-payment').val())
            var voucher_no = self.$('#voucher-no').val()
            var voucherAmount = 0

            var cashregister = this.pos.get_order().selected_cashregister

            var order = this.pos.get_order()
            order.set_allow_press_payment_numpad(false)

            if (!voucher_id) {
                this.gui.show_popup('error', {
                    title: _t('Invalid Value'),
                    body: _t(
                        'You must select a valid voucher'
                    ),
                })
                return
            }
            else if (!voucher_no) {
                this.gui.show_popup('error', {
                    title: _t('Invalid Value'),
                    body: _t(
                        'You must input voucher number'
                    ),
                })
                return
            }
            else {
                this.gui.close_popup()
                var remainingAmount = order.get_due()

                var selected_voucher = self.pos.kg_vouchers.find(type => type.id === voucher_id)
                if (selected_voucher && selected_voucher.is_open_amount)
                {
                    voucherAmount = parseFloat(self.$('#voucher-amount').val())
                    if (!voucherAmount || voucherAmount < 0) {
                        this.gui.show_popup('error', {
                            title: _t('Invalid Value'),
                            body: _t(
                                'You must input a correct voucher amount'
                            ),
                        })
                        return
                    }
                    if (voucherAmount > remainingAmount) {
                        voucherAmount = remainingAmount
                    }
                } else {
                    voucherAmount = selected_voucher.amount
                }
                // TODO: voucher external jika nilai voucher > total order, how to handle it?

                order.add_paymentline(cashregister)
                var newPaymentLine = order.selected_paymentline
                newPaymentLine.voucher_id = voucher_id
                newPaymentLine.voucher_no = voucher_no
                newPaymentLine.voucher_model = selected_voucher
                newPaymentLine.set_amount(voucherAmount)

                this.pos.payment_widget.reset_input()
                this.pos.payment_widget.render_paymentlines()
            }
        },
        select_voucher: function(event) {
            var self = this
            var voucher_id = parseInt(self.$('#voucher-payment').val())
            if (!!voucher_id) {
                var selected_voucher = self.pos.kg_vouchers.find(type => type.id === voucher_id)
                if (!!selected_voucher && selected_voucher.is_open_amount) {
                    self.$('#voucher-amount').attr('readonly', false)
                    var remainingAmount = this.pos.get_order().get_due()
                    self.$('#voucher-amount').attr('max', remainingAmount)
                    self.$('#voucher-amount').val(remainingAmount)
                } else if (!!selected_voucher) {
                    self.$('#voucher-amount').val(selected_voucher.amount)
                    self.$('#voucher-amount').attr('readonly', true)
                }
            }
        },
        check_length: function(event) {
            const el = event.target
            if (el.value.length > el.max.length) {
                el.value = el.value.slice(0, el.max.length)
            }
        },

    })
    gui.define_popup({ name: 'kg-voucher', widget: VoucherPopup })
})
