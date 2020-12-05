odoo.define('kg_pos.no_ref', function(require) {
    'use_strict'

    var models = require('point_of_sale.models')
    var screens = require('point_of_sale.screens')
    var gui = require('point_of_sale.gui')
    var popups = require('point_of_sale.popups')
    var core = require('web.core')

    var _t = core._t

    var _super_order = models.Order.prototype
    models.Order = models.Order.extend({
        initialize: function() {
            _super_order.initialize.apply(this, arguments)

            this.no_reference = this.no_reference

            this.save_to_db()
        },
        export_as_JSON: function() {
            var json = _super_order.export_as_JSON.apply(this, arguments)
            // json.meal_time = this.meal_time ? this.meal_time.name : undefined
            json.no_reference = this.no_reference

            return json
        },
        init_from_JSON: function(json) {
            _super_order.init_from_JSON.apply(this, arguments)

            this.no_reference = json.no_reference

        },
        export_for_printing: function() {
            var json = _super_order.export_for_printing.apply(this, arguments)

            json.no_reference = this.no_reference

            return json
        },
        set_no_ref: function(no_reference) {
            this.no_reference = no_reference
            this.trigger('change')
        },
        get_no_ref: function() {
            return {
                no_reference: this.no_reference,
            }
        },
    })


    var NoRefWidget = popups.extend({
        template: 'NoRefWidget',
        show: function(options) {
            var self = this
            options = options || {}
            this._super(options)

            var order = self.pos.get_order()
            this.no_reference = order.no_reference

            this.renderElement()
        },
        click_confirm: function(event) {
            var noReference = this.$('#no-reference').val()

            this.pos
                .get_order()
                .set_no_ref(noReference)

            this.gui.close_popup()
        },

    })
    gui.define_popup({ name: 'no-ref', widget: NoRefWidget })

    var NoRefButton = screens.ActionButtonWidget.extend({
        template: 'NoRefButton',
        button_click: function() {
            var self = this
            this.gui.show_popup('no-ref', {
                title: _t('Reference Number'),
                cheap: true,
            })
        },
        renderElement: function(){
            var self = this;
            if (!self.pos.config.iface_floorplan) {
                this._super();
            }
        },
    })

    screens.define_action_button({
        name: 'no-ref-button',
        widget: NoRefButton,
    })

})
