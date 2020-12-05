odoo.define('kg_banquet.pms_room_rate_field', function(require) {
"use strict";

var core = require('web.core');
var Dialog = require('web.Dialog');
var field_registry = require('web.field_registry');
var customSearchPmsField = field_registry.get('kg_field_pms_custom_search_base');

var _t = core._t;

var kgFieldPmsRoomRateInfo = customSearchPmsField.extend({
    widget_class: 'oe_form_field_kg_field_room_rate_info',
    // className: 'oe_form_field_kg_field_guest_info',
    resetOnAnyFieldChange: true,
    init: function() {
        // this.id_for_label = 'input_guest_info_pms'
        this._super.apply(this, arguments);
        this.searchModelName = 'banquet.reservation.resident'
        this.searchMethodName = 'search_room_rate_pms'

    },

     _getFields: function() {
        return [
            { name: "RateId", type: "text", width: 100 },
            { name: "Description", type: "number", width: 100},
            { name: "RoomRate", type: "text", width: 100 },
            ]
            },
    _render: function() {
        // called after rendering finished
        // https://www.odoo.com/documentation/11.0/reference/javascript_reference.html
        var self = this;
        console.log(self.recordData)
        return this._super.apply(this, arguments);
    },
    formatData: function(data) {
        // override this function, define display and data value based on json data
        this.displayName = `${data.RateId}`;
        this.dataValue = `${data.RateId}--${data.RoomRate}--${data.ExtraBedCharge}`;
    },
    _initiateData: function() {
        // override this function, define value from existing fields
        this.displayName = `${this.recordData['room_rate_id']}`;
        this.dataValue = `${this.recordData['room_rate_id']}--${this.recordData['amount']}--${this.recordData['extra_bed_charge']}`;
        // important, set value
        this.value = `${this.recordData['room_rate_id']}`;
    },
    setSearchKwargs: function($content) {
        var self = this
        var $searchParamElement = $content.find('#kg_field_search_param')
        var $searchParamElementPerson = $content.find('#kg_field_search_person')
        var searchParam = $searchParamElement.val()
        var searchPerson = $searchParamElementPerson.val()
        if (core.debug) {
          console.log('person:',this.recordData['room_type_id'], this.recordData['rate_type_id'].data)
        }
        if (!this.recordData['person']) {
            self.do_warn(_t("Error"), _t("Please define 'Person'!"));
            return false
        }
        if (!this.recordData['rate_type_id'] || !this.recordData['rate_type_id'].data) {
            self.do_warn(_t("Error"), _t("Please define 'Rate Type'!"));
            return false
        }
        if (!this.recordData['room_type_id'] || ! this.recordData['room_type_id'].data) {
            self.do_warn(_t("Error"), _t("Please define 'Room Type'!"));
            return false
        }
        if (!this.recordData['arrival_date']) {
            self.do_warn(_t("Error"), _t("Please define 'Arrival Date'!"));
            return false
        }
        return {
            search: searchParam,
            person: this.recordData['person'],
            rate_type: this.recordData['rate_type_id'].data.id,
            room_type: this.recordData['room_type_id'].data.id,
            arrival_date: this.recordData['arrival_date']
        }
    },
});

field_registry.add('kg_field_pms_room_rate_info', kgFieldPmsRoomRateInfo);

return {
    kgFieldPmsRoomRateInfo: kgFieldPmsRoomRateInfo,
};

});