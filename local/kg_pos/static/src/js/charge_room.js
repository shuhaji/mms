odoo.define('kg_pos.charge_room', function(require) {
    'use_strict'

    var models = require('point_of_sale.models')
    var screens = require('point_of_sale.screens')
    var gui = require('point_of_sale.gui')
    var popups = require('point_of_sale.popups')
    var core = require('web.core')
    var rpc = require('web.rpc')

    var _t = core._t

    models.load_fields("res.company",
        [
            'currency_id',
            'email',
            'website',
            'company_registry',
            'vat',
            'name',
            'phone',
            'partner_id',
            'country_id',
            'tax_calculation_rounding_method',
            'hotel_id',
        ]);

    var _super_order = models.Order.prototype
    models.Order = models.Order.extend({
        initialize: function() {
            _super_order.initialize.apply(this, arguments)

            this.folio_id = this.folio_id
            this.room_number = this.room_number
            this.folio_owner = this.folio_owner
            this.folios = this.folios

            this.save_to_db()
        },
        export_as_JSON: function() {
            var json = _super_order.export_as_JSON.apply(this, arguments)

            json.folio_id = this.folio_id
            json.room_number = this.room_number
            json.folio_owner = this.folio_owner
            json.folios = this.folios

            return json
        },
        init_from_JSON: function(json) {
            _super_order.init_from_JSON.apply(this, arguments)

            this.folio_id = json.folio_id
            this.room_number = json.room_number
            this.folio_owner = json.folio_owner
            this.folios = json.folios
        
        },
        export_for_printing: function() {
            var json = _super_order.export_for_printing.apply(this, arguments)

            json.folio_id = this.folio_id
            json.room_number = this.room_number
            json.folio_owner = this.folio_owner
            json.folios = this.folios

            return json
        },
        set_folio: function(folio_id, room_number, folio_owner) {
            this.folio_id = folio_id
            this.room_number = room_number
            this.folio_owner = folio_owner

            this.trigger('change')
        },
        set_folio_data: function(folio_data) {
            this.folios = folio_data

            this.trigger('change')
        },
        get_folio_data: function() {
            return {
                folios: this.folios
            }
        },
        get_folio: function() {
            if (this.folio_id && this.room_number) {
                return {
                    folio_id: this.folio_id,
                    room_number: this.room_number,
                    folio_owner: this.folio_owner,
                }
            }

            return null
        },
    })

    var ChargeRoomWidget = popups.extend({
        template: 'ChargeRoomWidget',
        show: function(options) {
            var self = this
            options = options || {}

            var folio = this.pos.get_order().get_folio()
            this.enable_keypress = true
            this.folios = []

            this._super(options)
            self.renderElement()

            if (folio) {
                this.room_number = folio.room_number
                this.folio_id = folio.folio_id

                rpc.query({
                    model: 'pos.helpers',
                    method: 'get_folio',
                    args: [folio.room_number],
                }).then(function(response) {
                    var folios = []

                    if (response.length > 0) {
                        for (var i = 0; i < response.length; i++) {
                            folios.push(response[i])
                        }
                    }
                    
                    self.folios = folios
                    // self.pos.get_order().set_folio_data(folios[0])
                    
                    self.$('#folio-div').removeClass('oe_hidden')
                    self.$('#confirm-charge-room').removeClass('oe_hidden')

                })
            }

            self.$('#room-number').keypress(function(event) {
                self.search_room_handler(event, $(this))
            })
            self.$('#folio').change(function(event) {
                self.select_folio_handler(event)
            })
            self.$('#get_folios').click(function() {
                //console.log('clicked')
                self.click_get_folios()
            });
        },
        search_room_handler: function(event, $el) {
            if (event.key === 'Enter') {
                this.click_get_folios()
            }
        },
        click_get_folios: function() {
            //console.log('clicked 2')
            var self = this

            var folio_div = $('#folio-div')
            var folio_field = $('#folio')
            var not_found_msg = $('#folio-not-found')
            var error_msg = $('#error-msg')

            folio_div.addClass('oe_hidden')
            not_found_msg.addClass('oe_hidden')
            error_msg.addClass('oe_hidden')

            self.folios = []
            var room_number = parseInt(self.$('#room-number').val())
            if (!!room_number) {
                rpc.query({
                    model: 'pos.helpers',
                    method: 'get_folio',
                    args: [room_number],
                }).then(function(response) {
                    if (response.error) {
                         error_msg.html(response.error.message)
                         error_msg.removeClass('oe_hidden')
                         return
                     }
                    var options = ['<option/>']
                    if (response.length > 0) {
                        for (var i = 0; i < response.length; i++) {
                            var folio = response[i]
                            self.folios.push(folio)
                            options.push(
                                `<option value=${folio.FolioId}>` +
                                    `${folio.FolioId} - ${folio.GuestName}` +
                                    '</option>'
                            )
                        }

                        // posmodel.get_order().set_folio_data(folio)

                        folio_field.empty().append(options)
                        folio_div.removeClass('oe_hidden')
                    } else {
                        not_found_msg.removeClass('oe_hidden')
                    }
                })
            }
        },
        select_folio_handler: function(event) {
            var confirm_button = $('#confirm-charge-room')
            if (event.target.value) {
                confirm_button.removeClass('oe_hidden')
            } else {
                confirm_button.addClass('oe_hidden')
            }
        },
        click_confirm: function(event) {
            var self = this

            var room_number = parseInt(self.$('#room-number').val())
            var selected_folio_id = parseInt(self.$('#folio').val())
            console.log(room_number, selected_folio_id, self.folios)
            if (!!room_number && !!selected_folio_id && self.folios.length > 0) {
                selected_folio = self.folios.find(obj => obj.FolioId === selected_folio_id)
                if (!!selected_folio) {
                    var order = self.pos.get_order()
                    order.set_allow_press_payment_numpad(true)

                    // assign folio object to order (follow old code algorithm)
                    order.set_folio_data(selected_folio)
                    // set folio info to order
                    order.set_folio(selected_folio.FolioId, room_number, selected_folio.GuestName)
                    self.gui.close_popup()

                    order.add_paymentline(order.selected_cashregister)
                    this.pos.payment_widget.reset_input()
                    this.pos.payment_widget.render_paymentlines()
                }
            }
        },
    })

    gui.define_popup({ name: 'charge-room', widget: ChargeRoomWidget })
})
