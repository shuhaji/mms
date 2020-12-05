odoo.define('kg_banquet.pms_guest_field', function(require) {
"use strict";

var core = require('web.core');
var Dialog = require('web.Dialog');
var field_registry = require('web.field_registry');
var customSearchPmsField = field_registry.get('kg_field_pms_custom_search_base');

var _t = core._t;

var kgFieldPmsGuestInfo = customSearchPmsField.extend({
    widget_class: 'oe_form_field_kg_field_guest_info',
    // className: 'oe_form_field_kg_field_guest_info',
    init: function() {
        // this.id_for_label = 'input_guest_info_pms'
        this._super.apply(this, arguments);
        this.searchModelName = 'banquet.reservation.resident'
        this.searchMethodName = 'search_guest_pms'
        this.searchTemplate = 'kg_banquet.dialogSearchGuestFromPMS'
    },

      _getFields: function() {
        return [
            { name: "GuestId", type: "text", width: 50, validate: "required"},
            { name: "GuestName", type: "text", width: 100},
            { name: "company_name", type: "text", width: 100 },
            { name: "sip_number", type: "text", width: 100 },
            { name: "MobilePhone", type: "text", width: 100 },
            { name: "EmailAddress", type: "text", width: 100 },
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
        this.displayName = `${data.GuestName}`;
        this.dataValue = `${data.GuestId}--${data.GuestName}`;
    },
    _initiateData: function() {
        // override this function, define value from existing fields
        this.displayName = `${this.recordData['guest_name']}`;
        this.dataValue = `${this.recordData['guest_pms_id']}--${this.recordData['guest_name']}`;
        // important, set value
        this.value = `${this.recordData['guest_name']}`;
    },
    setSearchKwargs: function($content) {
        var self = this
        var $searchParamElementName = $content.find('#kg_field_search_param_name')
        var $searchParamElementEmail = $content.find('#kg_field_search_param_email')
        var $searchParamElementPhone = $content.find('#kg_field_search_param_phone')
        var searchParamName = $searchParamElementName.val()
        var searchParamEmail = $searchParamElementEmail.val()
        var searchParamPhone = $searchParamElementPhone.val()
        return {
            name: searchParamName,
            email : searchParamEmail,
            phone : searchParamPhone
        }
    },
});

field_registry.add('kg_field_pms_guest_info', kgFieldPmsGuestInfo);

return {
    kgFieldPmsGuestInfo: kgFieldPmsGuestInfo,
};

});