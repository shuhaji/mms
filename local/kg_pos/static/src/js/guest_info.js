odoo.define('kg_pos.guest_info', function(require) {
    'use_strict'

    var models = require('point_of_sale.models')
    var screens = require('point_of_sale.screens')
    var gui = require('point_of_sale.gui')
    var popups = require('point_of_sale.popups')
    var core = require('web.core')

    var _t = core._t

    models.load_models({
        model: 'meal.time',
        field: ['name'],
        loaded: function(self, meal_times) {
            // custom code by andi
            valid_meal_time = []
            for (var i = 0; i < meal_times.length; i++) {
                if (meal_times[i].id === self.config.meal_time_id[0]) {
                    valid_meal_time.push(meal_times[i])
                }
            }
            self.meal_times = meal_times
            self.meal_time = valid_meal_time
            self.meal_time_by_id = {}
            for (var i = 0; i < self.meal_times.length; i++) {
                self.meal_time_by_id[self.meal_times[i].id] = self.meal_times[i]
            }

            // end of custom code

            // original code by reza
            // self.meal_types = meal_types
            // self.meal_type_by_id = {}
            // for (var i = 0; i < meal_times.length; i++) {
            //     self.meal_type_by_id[meal_times[i].id] = meal_times[i]
            // }
        },
    })

    models.load_models({
        model: 'meal.time.line',
        field: ['meal_type', 'start', 'end'],
        loaded: function(self, meal_time_lines) {
            var valid_meal_time_lines = []

            if (self.meal_time.length > 0) {
                for (var i = 0; i < meal_time_lines.length; i++) {
                    if (
                        meal_time_lines[i].meal_time_id[0] === self.meal_time[0].id
                    ) {
                        valid_meal_time_lines.push(meal_time_lines[i])
                    }
                }
            }
            self.meal_time_lines = valid_meal_time_lines
        },
    })

    var _super_order = models.Order.prototype
    models.Order = models.Order.extend({
        initialize: function() {
            _super_order.initialize.apply(this, arguments)

            this.meal_time_lines = this.meal_time_lines
            this.meal_time_id = this.meal_time_id
            this.no_reference = this.no_reference
            this.meal_time_line_id = this.get_current_meal_time()
            this.is_hotel_guest = true

            this.save_to_db()
        },
        export_as_JSON: function() {
            var json = _super_order.export_as_JSON.apply(this, arguments)
            // json.meal_time = this.meal_time ? this.meal_time.name : undefined
            json.meal_time_lines = this.meal_time_lines
            json.meal_time_line_id = this.meal_time_line_id
            json.no_reference = this.no_reference
            json.is_hotel_guest = this.is_hotel_guest

            return json
        },
        init_from_JSON: function(json) {
            _super_order.init_from_JSON.apply(this, arguments)

            this.meal_time_lines = json.meal_time_lines
            this.meal_time_line_id = json.meal_time_line_id
            this.no_reference = json.no_reference
            this.is_hotel_guest = json.is_hotel_guest
        },
        export_for_printing: function() {
            var json = _super_order.export_for_printing.apply(this, arguments)

            json.meal_time_lines = this.meal_time_lines
            json.meal_time_line_id = this.meal_time_line_id
            json.no_reference = this.no_reference
            json.is_hotel_guest = this.is_hotel_guest
            return json
        },
        set_guest_info: function(
            no_reference,
            meal_time_line_id,
            is_hotel_guest
        ) {
            this.no_reference = no_reference
            this.meal_time_line_id = meal_time_line_id
            this.is_hotel_guest = is_hotel_guest
            this.trigger('change')
        },
        get_guest_info: function() {
            return {
                no_reference: this.no_reference,
                meal_time_line_id: this.meal_time_line_id,
                is_hotel_guest: this.is_hotel_guest,
            }
        },
        get_current_meal_time: function() {
            var self = this
            var date = new Date()
            var hour = date.getHours()
            var minute = date.getMinutes()
            var decimal_point = minute / 100
            var current_hour = hour + decimal_point
            var current_meal_time = null

            for (var i = 0; i < self.pos.meal_time_lines.length; i++) {
                if (self.pos.meal_time_lines[i].end !== 0.0) {
                    if (
                        self.pos.meal_time_lines[i].start <= current_hour &&
                        current_hour <= self.pos.meal_time_lines[i].end
                    ) {
                        current_meal_time = self.pos.meal_time_lines[i].id
                    }
                } else {
                    if (
                        self.pos.meal_time_lines[i].start <= current_hour &&
                        current_hour <= 24
                    ) {
                        current_meal_time = self.pos.meal_time_lines[i].id
                    }
                }
            }

            return current_meal_time
        },
    })

    var GuestInfoWidget = popups.extend({
        template: 'GuestInfoWidget',
        show: function(options) {
            var self = this
            options = options || {}
            this._super(options)
            var order = self.pos.get_order()
            var current_meal_time = order.get_current_meal_time()
            console.log('self', self)

            this.no_reference = order.no_reference
            this.meal_time_line_id = parseInt(order.meal_time_line_id)
            this.is_hotel_guest = order.is_hotel_guest

            if (order.meal_time_line_id) {
                this.meal_time_line_id = parseInt(order.meal_time_line_id)
            } else {
                this.meal_time_line_id = order.get_current_meal_time()
            }

            this.renderElement()
        },
        click_confirm: function(event) {
            var noReference = this.$('#guest-no-reference').val()
            var mealTimeLine = this.$('#meal-time-line').val()
            var isHotelGuest = this.$('#is-hotel-guest').is(':checked')

            this.pos
                .get_order()
                .set_guest_info(
                    noReference,
                    parseInt(mealTimeLine),
                    isHotelGuest
                )

            this.gui.close_popup()
        },
    })
    gui.define_popup({ name: 'guest-info', widget: GuestInfoWidget })

    var GuestInfoButton = screens.ActionButtonWidget.extend({
        template: 'GuestInfoButton',
        button_click: function() {
            var self = this
            this.gui.show_popup('guest-info', {
                title: _t('Guest Info'),
                cheap: true,
            })
        },
        renderElement: function() {
            var self = this
            if (self.pos.config.module_pos_restaurant) {
                this._super()
            }
        },
    })

    screens.define_action_button({
        name: 'guest-info-button',
        widget: GuestInfoButton,
    })
})
