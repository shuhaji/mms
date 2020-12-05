odoo.define('kg_web.custom_search_pms_field', function(require) {
"use strict";

var core = require('web.core');
var Dialog = require('web.Dialog');
var field_registry = require('web.field_registry');
var AbstractField = require('web.AbstractField');
var charField = field_registry.get('char');

var _t = core._t;

//var FormController = require('web.FormController');
//
//FormController.include({
//    _update: function () {
//        var _super_update = this._super.apply(this, arguments);
//        this.trigger('view_updated');
//        return _super_update;
//    },
//});

// TODO:
// di python:
//   + model : + field guest_info (char), akan menyimpan json string guest yg dipilih dari hasil search ke PMS
//   + saat on change guest info, isi guest id + name ke field guest id dan name jg
//   + method search_guest_pms_via_api utk search dg hit api pms (with parameter guest name)
// di Javascript:
//   + button utk show popup search ke pms
//   +   saat search : hit method search_guest_pms_via_api
//   +   saat confirm selection, set value selected json guest info ke field guest info ini

var kgFieldSearchPms = charField.extend({
    template: 'kgFieldCustomSearchFromPmsViewTemplate',
    widget_class: 'oe_form_field_kg_field_custom_search_pms',
    init: function() {
        // this.id_for_label = 'kg_field_search_on_pms_value'
        this.searchModelName = ''
        this.searchMethodName = ''
        this._super.apply(this, arguments);
        this.selectedRow = false
        this.currentSelectedRow = false
        this._initiateData()
        this.$dataGrid = null
        this.searchTemplate = 'kg_web.dialogSearchFromPMS'
    },
    _render: function() {
        // called after rendering finished
        // https://www.odoo.com/documentation/11.0/reference/javascript_reference.html
        var self = this;
        var renderResult = this._super.apply(this, arguments);
        self.$input = self.$el.find('.kg_field_search_on_pms_value');
        self._setDisplayValue()
        // console.log('input el: ', this.$input)
        return renderResult;
    },
    events: {
        'click .btn_show_search_from_pms': '_buttonShowSearchClicked',
    },
    formatData: function(data) {
        // override this function, define display and data value based on json data
        // example:
        this.displayName = `${data.Age}--${data.Name}`;
        this.dataValue = `${data.Age}--${data.Name}`;
    },
    _initiateData: function() {
        // override this function, define value from existing fields
        // example:
        this.displayName = `${this.recordData['guest_pms_id']}--${this.recordData['guest_name']}`;
        this.dataValue = `${this.recordData['guest_pms_id']}--${this.recordData['guest_name']}`;
        // important, set value
        this.value = this.dataValue
    },
    _setDisplayValue: function() {
        var self = this
//        if (core.debug) {
//            console.log(self.mode, self.displayName, self.$input, self.$el)
//        }
        if (self.mode === 'readonly') {
//            console.log('read only')
            self.$el.toggleClass('o_field_empty', false)
            self.$el.text(self.displayName)
        } else {
            console.log('self input',self.$input)
            self.$input.val(self.displayName)
        }

        console.log('onchange parent')
    },
    _getFields: function(data) {
        // TODO: override this function, define fields for result table/grid
        return this._getFieldsBasedOnData(data)
    },
    _getFieldsBasedOnData: function(data) {
        var fields = []
        if (!!data && Array.isArray(data) && data.length > 0 ) {
            var obj = data[0]
            for (var prop in obj) {
                if (Object.prototype.hasOwnProperty.call(obj, prop)) {
                    // do stuff
                    var field = { name: prop, type: "text", width: "auto"};
                    fields.push(field)
                }
            }
        }
        return fields
    },
    _getInputElement: function() {
        return this.$('#' + this.id_for_label)
    },
    _buttonShowSearchClicked: function(e) {
        var self = this
        this._showSearchDialog()
    },
    _buttonDoSearchClicked: function(e) {
        this.doSearch()
    },
    setSearchKwargs: function($content) {
        var self = this
        var $searchParamElement = $content.find('#kg_field_search_param')
        var searchParam = $searchParamElement.val()
        return {
            search: searchParam
        }
    },
    doSearch: function(searchParamKwargs) {
        var self = this
        // console.log(searchParam, self.searchModelName, self.searchMethodName)
        var def = $.Deferred();
        var data = []
        // var searchArgs = self.setSearchArgs(searchParam)
        if (!!searchParamKwargs) {
            // search with rpc
            self._rpc({
                model: self.searchModelName,
                method: self.searchMethodName,
                kwargs: searchParamKwargs
            }).then(function (result) {
                if (core.debug) {
                    console.log('search data pms - result', result)
                }
                var fields = self._getFields(result)
                self.displayGrid(result, fields)
                def.resolve();
            }).fail(function (error, event) {
                event.preventDefault();
                if (core.debug) {
                    console.log('failed to search data pms', error, event)
                }
                if (!(error && error.code === 200 && error.data.exception_type)) {
                    self.do_warn(_t("Error"), _t(" Failed to search data"));
                } else {
                    self.do_warn(_t("Error"), _t(" Failed to search data, Error: ") + error.data.message);
                }
            });
        }
        return data;
    },
    displayGrid: function(data, fields) {
        var self = this
        // http://js-grid.com/
        if (core.debug) {
            console.log('data', data, 'fields', fields)
        }
        var searchGrid = self.$dataGrid.jsGrid({
            width: "100%",
            height: "auto",

            inserting: false,
            editing: false,
            sorting: true,
            paging: true,
            rowClick: function(args) {
                // console.log('select: ', args)
                self.currentSelectedRow = args.item

                var $row = this.rowByItem(args.item),
                    selectedRow = $("#jsGridKgCustomSelection").find('table tr.jsgrid-highlight-1');

                if (selectedRow.length) {
                    selectedRow.toggleClass('jsgrid-highlight-1');
                };

                $row.toggleClass("jsgrid-highlight-1");
            },
//            rowDoubleClick: function(args) {
//                console.log('doubleClick: ', args)
//                self.selectedRow = args.item
//            },

            data: data,
            fields: fields
        });
    },
    confirmSelection: function(data) {
//        console.log(this.$input)
        console.log('klik select')
        if (!!data) {
            // console.log('select confirm', data)
            this.selectedRow = data
            this.formatData(data)
            if (core.debug) {
                console.log('data value: ', this.dataValue, 'display name: ', this.displayName)
            }
            // update current value with this data
            this._setValue(this.dataValue)
            this._setDisplayValue(this.displayName)
         }
    },
    searchButtonClick: function($content) {
        var self = this
        // set variable dataGrid to current class instance
        self.$dataGrid = $content.find('#jsGridKgCustomSelection')
        var searchKwargs = self.setSearchKwargs($content)
        if (!!searchKwargs) {
            self.doSearch(searchKwargs)
        }
    },
    _showSearchDialog: function() {
        var self = this

        var $content = $(core.qweb.render(self.searchTemplate, {}
//            {
//                cover_id: coverID,
//                attachment_ids: attachment_ids,
//            }
        ));
        var dialog = new Dialog(self, {
            title: _t("Search"),
            buttons: [
              {text: _t("Select/Confirm"), classes: 'btn-primary', close: true,
                disabled: false,
                click: function () {
                    self.confirmSelection(self.currentSelectedRow);
                }},
              {text: _t("Cancel"), close: true}],
            $content: $content,
        });
        dialog.opened().then(function () {
            var $searchBtn = $content.find('#btn_do_search_custom_pms');
            if (!!$searchBtn) {
                $searchBtn.click(function() {
                    self.searchButtonClick($content)
                })
            }

            var $selectBtn = dialog.$footer.find('.btn-primary');
            // todo: saat salah satu row di click, set button confirm disabled jadi false
//            $content.on('click', 'img', function (ev) {
//                $imgs.not(ev.currentTarget).removeClass('o_selected');
//                $selectBtn.prop('disabled', !$(ev.currentTarget).toggleClass('o_selected').hasClass('o_selected'));
//            });

        });
        dialog.open();
    },
    _grid_dummy: function() {
        var self = this
        var clients = [
            { "Name": "Otto Clay", "Age": 25, "Country": 1, "Address": "Ap #897-1459 Quam Avenue", "Married": false },
            { "Name": "Connor Johnston", "Age": 45, "Country": 2, "Address": "Ap #370-4647 Dis Av.", "Married": true },
            { "Name": "Lacey Hess", "Age": 29, "Country": 3, "Address": "Ap #365-8835 Integer St.", "Married": false },
            { "Name": "Timothy Henson", "Age": 56, "Country": 1, "Address": "911-5143 Luctus Ave", "Married": true },
            { "Name": "Ramona Benton", "Age": 32, "Country": 3, "Address": "Ap #614-689 Vehicula Street", "Married": false }
        ];
        var countries = [
            { Name: "", Id: 0 },
            { Name: "United States", Id: 1 },
            { Name: "Canada", Id: 2 },
            { Name: "United Kingdom", Id: 3 }
        ];
        var fields = self._getDummyFields()
        self.displayGrid(clients, fields)
//        self.renderElement();
//        $('#kg_field_pms_guest_search').dialog()
    },
    _getDummyFields: function() {
        return [
            { name: "Name", type: "text", width: 150, validate: "required" },
            { name: "Age", type: "number", width: 50 },
            { name: "Address", type: "text", width: 200 },
            { name: "Country", type: "select", items: countries, valueField: "Id", textField: "Name" },
            { name: "Married", type: "checkbox", title: "Is Married", sorting: false },
//                { type: "control" }
        ]
    },

});

field_registry.add('kg_field_pms_custom_search_base', kgFieldSearchPms);

return {
    kgFieldSearchPms: kgFieldSearchPms,
};

});