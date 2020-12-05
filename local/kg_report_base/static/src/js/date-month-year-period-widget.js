odoo.define('kg_report_base.dateMonthYearPeriodWidget', function(require) {
"use strict";

var field_registry = require('web.field_registry');
var field_utils = require('web.field_utils');
var basicFields = require('web.basic_fields');

var dateMonthYearPeriodWidget = basicFields.InputField.extend({
    template: 'dateMonthYearPeriodWidget',
    className: 'oe_form_field_date_month_year_period_widget',
    init: function() {
        this._super.apply(this, arguments);
    },
    start: function() {
        this.$input = this.$('input.o_date_month_year_period_input');
        // var today = new Date().toISOString().split('T')[0]
        // var value = today.substr(0, 7)
        // console.log('start', value, this.value._i, this.value)
        if (Date.parse(this.value._i)) {
            var today = this.value._i.split('T')[0]
            var value = today.substr(0, 7)
            // console.log('start 2', value2)
            this.$input.val(value);
        }
    },
    _onChange: function () {
        this._super.apply(this, arguments);
        // console.log(this.value, this.$input.val())
    },
//    events: {
//        'click .btn': '_button_clicked',
//    },
//    _button_clicked: function(e) {
//        // this._setValue(parseInt(jQuery(e.target).attr('data-id')));
//    },
    _render: function() {
        // this.renderElement();
//        var self = this;
//        var reportData = JSON.parse(this.value);
        this.renderElement();
    },
    /**
     * @private
     * @param {Moment} v
     * @returns {string}
     */
    _formatClient: function (v) {
        return moment(v, 'YYYY-MM');
    },
});

field_registry.add('date-month-year-period-widget', dateMonthYearPeriodWidget);

return {
    dateMonthYearPeriodWidget: dateMonthYearPeriodWidget,
};

});