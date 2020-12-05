odoo.define('kg_pos.choose_waiter', function(require) {
    'use_strict'

    var models = require('point_of_sale.models')
    var screens = require('point_of_sale.screens')
    var gui = require('point_of_sale.gui')
    var popups = require('point_of_sale.popups')
    var core = require('web.core')
    var field_utils = require('web.field_utils')
    var utils = require('web.utils');

    var _t = core._t
    var round_pr = utils.round_precision;
    var QWeb = core.qweb;

    models.load_models({
        model: 'hr.employee',
        loaded: function(self, employee) {
            self.waiter = []
            for (var i = 0; i < employee.length; i++) {
                if (employee[i].waiter) {
                    self.waiter.push(employee[i]) 
                }
            }
            
            // used when choosing waiter by its job_position field in employee menu
            // self.waiter = self.waiter.filter(waiter => ['waiters', 'waiter'].includes(waiter.job_id[1].toLowerCase()))
            // end of code
        }
    })

    var _super_order = models.Order.prototype
    models.Order = models.Order.extend({
        initialize: function() {
            _super_order.initialize.apply(this, arguments)

            this.waiter = this.waiter

            this.save_to_db()
        },
        export_as_JSON: function() {
            var json = _super_order.export_as_JSON.apply(this, arguments)
            // json.meal_time = this.meal_time ? this.meal_time.name : undefined
            json.waiter = this.waiter

            return json
        },
        init_from_JSON: function(json) {
            _super_order.init_from_JSON.apply(this, arguments)

            this.waiter = json.waiter

        },
        export_for_printing: function() {
            var json = _super_order.export_for_printing.apply(this, arguments)

            json.waiter = this.waiter

            return json
        },
        set_waiter: function(waiter) {
            this.waiter = waiter
            this.trigger('change')
        },
        get_waiter: function() {
            return {
                waiter: this.waiter,
            }
        },
    })

    var ChooseWaiterWidget = popups.extend({
        template: 'ChooseWaiterWidget',
        show: function(options) {
            var self = this
            options = options || {}
            this._super(options)

            var order = self.pos.get_order()
            this.waiter_selected = order.waiter
            
            this.renderElement()
        },
        click_confirm: function(event) {
            var waiter = false
            var waiter = parseInt(this.$('#waiter').val())
            
            for (var i = 0; i < this.pos.waiter.length; i++) {
                if (this.pos.waiter[i].id === waiter) {
                    waiter = this.pos.waiter[i]
                }
            }
            
            this.pos
                .get_order()
                .set_waiter(waiter)

            this.gui.close_popup()
        },

    })
    gui.define_popup({ name: 'choose-waiter', widget: ChooseWaiterWidget })

    var ChooseWaiterButton = screens.ActionButtonWidget.extend({
        template: 'ChooseWaiterButton',
        button_click: function() {
            var self = this
            this.gui.show_popup('choose-waiter', {
                title: _t('Choose Waiter'),
                cheap: true,
            })
        },
        renderElement: function(){
            var self = this;
            if (self.pos.config.iface_floorplan) {
                this._super();
            }
        },
    })

    screens.define_action_button({
        name: 'choose-waiter-button',
        widget: ChooseWaiterButton,
    })
})
