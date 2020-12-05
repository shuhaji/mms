odoo.define('kg_pos.pms_room_info', function(require) {
"use strict";

var core = require('web.core');
var Dialog = require('web.Dialog');
var field_registry = require('web.field_registry');
var customSearchPmsField = field_registry.get('kg_field_pms_custom_search_base');

var _t = core._t;

var kgFieldPmsRoomInfo = customSearchPmsField.extend({
    widget_class: 'oe_form_field_kg_field_room_info_meals',
    // className: 'oe_form_field_kg_field_guest_info',
    resetOnAnyFieldChange: true,
    init: function() {
        // this.id_for_label = 'input_guest_info_pms'
        this._super.apply(this, arguments);
        this.searchModelName = 'wizard.pos.meal.allocation'
        this.searchMethodName = 'search_guest_info'
        this.searchTemplate = 'kg_web.dialogSearchFromPMS'
    },
    _render: function() {
        // called after rendering finished
        // https://www.odoo.com/documentation/11.0/reference/javascript_reference.html
        var self = this;
        console.log(self.recordData)
        return this._super.apply(this, arguments);
//        var self = this;
//        var renderResult = this._super.apply(this, arguments);
//        self.$input = self.$el.find('#kg_field_room_no');
//        self._setDisplayValue()
//        // console.log('input el: ', this.$input)
//        return renderResult;
    },
    formatData: function(data) {
        var self = this
        // override this function, define display and data value based on json data
        self.displayName = `${data.RoomNo}`;
        self.dataValue = `${data.RoomNo}--${data.GuestName}--${data.GuestStatusDescription}--
                          ${data.Person}--${data.ArrivalDate}--${data.DepartureDate}--
                          ${data.ExtraBed}--${data.RateType}--${data.TypeId}--
                          ${data.ReservationId}`;
        //$('#o_field_input_208').val(self.displayName)
    },
    _initiateData: function() {
        // override this function, define value from existing fields
        this.displayName = `${this.recordData['room_no']}`;
        this.dataValue = `${this.recordData['room_no']}--${this.recordData['guest_name']}--${this.recordData['guest_status']}--
                          ${this.recordData['person']}--${this.recordData['arrival_date']}--${this.recordData['departure_date']}--
                          ${this.recordData['extra_bed']}`;
        // important, set value
        this.value = `${this.recordData['room_no']}--${this.recordData['guest_name']}--${this.recordData['guest_status']}--
                      ${this.recordData['person']}--${this.recordData['arrival_date']}--${this.recordData['departure_date']}--
                      ${this.recordData['extra_bed']}`;
    },
    setSearchKwargs: function($content) {
        var self = this
        var $searchParamElement = $content.find('#kg_field_search_param')
        var searchParam = $searchParamElement.val()
//        var working_date = this.field_manager.get_field_value("working_date")

        return {
            search: searchParam,
            date: this.recordData['working_date']
//            date: working_date
        }
    },

    _getFields: function(data) {
        // TODO: override this function, define fields for result table/grid
        return [
            { name: "RoomNo", type: "text", width: "auto", validate: "required" },
            { name: "GuestName", type: "text", width: "auto" },
            { name: "GuestStatusDescription", type: "text", width: "auto" },
            { name: "Person", type: "number", width: "auto" },
            { name: "ArrivalDate", type: "text", width: "auto" },
            { name: "DepartureDate", type: "text", width: "auto" },
            { name: "ExtraBed", type: "number", width: "auto" },
            // { name: "Country", type: "select", items: countries, valueField: "Id", textField: "Name" },
//            { name: "Married", type: "checkbox", title: "Is Married", sorting: false },
//            { type: "control" }
        ]
    },
});

field_registry.add('kg_field_room_info_meals', kgFieldPmsRoomInfo);

return {
    kgFieldPmsRoomInfo: kgFieldPmsRoomInfo,
};

});