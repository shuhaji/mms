odoo.define('kg_pos.chrome', function(require) {
    'use strict'

    var chrome = require('point_of_sale.chrome')
    var models = require('point_of_sale.models')
    var session = require('web.session')

    models.load_models({
        model: 'res.users',
        fields: [
            'allow_void_bill',
            'company_id'
        ],
        ids: function(self) {
            return [session.uid]
        },
        loaded: function(self, users) {
            self.user.allow_void_bill = users[0].allow_void_bill
            self.user.company_id = users[0].company_id
        },
    })

    chrome.OrderSelectorWidget.include({
        renderElement: function() {
            var self = this

            self._super()
            if (!self.pos.user.allow_void_bill) {
                this.$('.deleteorder-button').addClass('oe_hidden')
            }
        },
    })
})
