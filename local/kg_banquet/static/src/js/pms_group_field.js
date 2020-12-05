odoo.define('kg_banquet.pms_group_field', function(require) {
"use strict";

var core = require('web.core');
var Dialog = require('web.Dialog');
var field_registry = require('web.field_registry');
var customSearchPmsField = field_registry.get('kg_field_pms_custom_search_base');

var _t = core._t;

var kgFieldPmsGroupInfo = customSearchPmsField.extend({
    widget_class: 'oe_form_field_kg_field_group_info',
    // className: 'oe_form_field_kg_field_guest_info',
    init: function() {
        // this.id_for_label = 'input_guest_info_pms'
        this._super.apply(this, arguments);
        this.searchModelName = 'banquet.reservation.resident'
        this.searchMethodName = 'search_group_pms'
    },
    _render: function() {
        // called after rendering finished
        // https://www.odoo.com/documentation/11.0/reference/javascript_reference.html
        var self = this;
        console.log(self.recordData)
        return this._super.apply(this, arguments);
    },
    _getFields: function() {
        return [
            { name: "GroupId", type: "number", width: 50, validate: "required"},
            { name: "GroupDescription", type: "text", width: 150 },
            { name: "CompanyId", type: "text", width: 50 },
            { name: "CompanyName", type: "text", width: 200 },
            ]
            },
    formatData: function(data) {
        // override this function, define display and data value based on json data
        this.displayName = `${data.GroupDescription}`;
        this.dataValue = `${data.GroupId}--${data.GroupDescription}`;
    },
    _initiateData: function() {
        // override this function, define value from existing fields
        this.displayName = `${this.recordData['group_name']}`;
        this.dataValue = `${this.recordData['group_name']}`;
        // important, set value
        this.value = `${this.recordData['group_name']}`;
    },
    setSearchKwargs: function($content) {
        var self = this
        var $searchParamElement = $content.find('#kg_field_search_param')
        var searchParam = $searchParamElement.val()

        return {
            search: searchParam
        }
    },
});

field_registry.add('kg_field_pms_group_info', kgFieldPmsGroupInfo);

return {
    kgFieldPmsGroupInfo: kgFieldPmsGroupInfo,
};

});