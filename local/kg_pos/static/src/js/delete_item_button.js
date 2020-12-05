odoo.define('kg_pos.delete_item_button', function(require) {
    'use strict'

    var models = require('point_of_sale.models')
    var screens = require('point_of_sale.screens')
    var gui = require('point_of_sale.gui')
    var popups = require('point_of_sale.popups')
    var core = require('web.core')
    var rpc = require('web.rpc')

    var _t = core._t
    var session = require('web.session')

    models.load_fields("res.users", "allow_cancel_item");
//    models.load_models({
//        model: 'res.users',
//        fields: [
//            'allow_cancel_item',
//        ],
//        loaded: function(self, users) {
//            for (var i = 0; i < self.users.length; i++) {
//                for (var j = 0; j < users.length; j++) {
//                    if (self.users[i].id === users[j].id) {
//                        self.users[i].allow_cancel_item = users[j].allow_cancel_item
//                    }
//                }
//            }
//            self.allowed_to_delete_item = false
//        },
//    })

    screens.NumpadWidget.include({
        clickDeleteLastChar: function() {
            var self = this
            // var _super = this._super.bind(this);

            //block remove order line when order type is reservation
            if (_.has(self.order, 'is_reservation') && !!self.order.is_reservation){
                return false
            }
            else{
                // custom code
                if (this.pos.user.allow_cancel_item){
                    return this.state.deleteLastChar();
                }
                else if (!this.pos.user.allow_cancel_item) {
                    if (this.pos.allowed_to_delete) {
                        return this.state.deleteLastChar();
                    }
                    else if (!this.pos.allowed_to_delete) {
                        this.gui.show_popup('security-pin', {
                            title: _t('Security PIN'),
                            confirm: function() {
                                var pin = this.$('#pin').val()

                                // note: manager PIN is from users that inside group of POS (both manager or user) and based on company
                                var user_by_pin = this.pos.users.find(user =>
                                    user.pos_security_pin === pin && user.allow_cancel_item)
                                if (user_by_pin) {
                                    self.pos.allowed_to_delete = true
                                    self.state.deleteLastChar();

                                    self.gui.close_popup()
                                } else {
                                    this.gui.show_popup('error', {
                                        title: _t('Invalid PIN'),
                                        body: _t(
                                            'No valid user found for this PIN'
                                        ),
                                    })
                                }
                            },
                        })
                    }
                }

            }
            // end of custom code
            
            // original code
            // return this.state.deleteLastChar();
            // end of original code
        },
    })

    var SecurityPinPopup = popups.extend({
        template: 'SecurityPinPopup',
        show: function(options) {
            var self = this
            options = options || {}
            this._super(options)

            this.renderElement()
        },
    })
    gui.define_popup({ name: 'security-pin', widget: SecurityPinPopup })
})
