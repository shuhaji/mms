/* Based on: web_widget_timepicker
    Copyright 2016 Vividlab <http://www.vividlab.de>
 * Copyright 2017 Kaushal Prajapati <kbprajapati@live.com>
 * Copyright 2019 Alexandre Díaz <dev@redneboa.es>
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

 modified by Aan - CITIS Kompas Gramedia, Nov 2019
  -- original: field float to display as HH:mm time picker (data stored as float in db)
  -- modification: field Char (HH:mm) to time picker (Data stored as char HH:mm in db)
 */
/*
In the form view declaration, put widget='timepicker' attribute in the field tag::
    ...
    <field name="arch" type="xml">
        <form string="View name">
            ...
            <field name="name"/>
            <field name="mytimefieldname" widget="timepicker"/>
            ...
        </form>
    </field>
    ...
Additional bootstrap datetime-picker plugin options can be specified by an options attribute::
    ...
    <field name="mytimefieldname" widget="timepicker" options="{'datepicker': {'stepping': 15}}"/>
    ...
See the available options at `datetime-picker <https://eonasdan.github.io/bootstrap-datetimepicker/Options/>`_.
*/
odoo.define('kg_web.web_widget_timepicker', function (require) {
    'use strict';

    var field_registry = require('web.field_registry');
    var field_utils = require('web.field_utils');
    var basic_fields = require('web.basic_fields');
    var datepicker = require('web.datepicker');
    var FieldDate = basic_fields.FieldDate;


    var TimeWidget = datepicker.DateTimeWidget.extend({
        type_of_date: "float_time",
//        type_of_date: "datetime",

        _onShow: function () {
            if (this.$input.val().length !== 0 && this.isValid()) {
                var value = this.$input.val();
                this.picker.date(new moment(value, this.options.format));
                this.$input.select();
            }
        },

        setValue: function (value) {
            // this.set({'value': value});
            var formatted_value = value ? this._formatClient(value) : null;
            this.set({'value': formatted_value});
            this.$input.val(formatted_value);
            if (this.picker) {
                var fdate = new moment(formatted_value, this.options.format);
                //console.log('setValue', value, formatted_value, fdate.isValid(), fdate, this.options.format)
                this.picker.date(fdate && fdate.isValid()
                    ? fdate : new moment());
            }
        },

        getValue: function () {
            var value = this.get('value');
            //if (!!value) console.log('getValue', value, this._formatClient(value))
            return value ? this._formatClient(value) : null;
        },

        changeDatetime: function () {
            if (this.isValid()) {
                var oldValue = this.getValue();
                this._setValueFromUi();
                var newValue = this.getValue();
                if (oldValue && newValue && newValue !== oldValue) {
                    this.trigger("datetime_changed");
                }
            }
        },
        /**
         * @private
         * @param {Moment} v
         * @returns {string}
         */
        _formatClient: function (v) {
            if (!!v && v instanceof moment) {
                return v.format(this.options.format)
            } else if (!!v && typeof(v) == 'string' && v.length < 6 && v.contains(':')) {
                return v
            } else {
                return field_utils.format[this.type_of_date](v, null, {timezone: false});
            }
//            return field_utils.format[this.type_of_date](v, null, {timezone: false});
        },
        _momentToHourMinute: function(v) {

        },
        /**
         * @private
         * @param {string|false} v
         * @returns {Moment}
         */
        _parseClient: function (v) {
            if (!!v && v.contains(':')) {
                // convert string 'HH:mm' to moment
                return new moment(v, this.options.format);
            } else {
                return field_utils.parse[this.type_of_date](v, null, {timezone: false});
            }
//            return field_utils.parse[this.type_of_date](v, null, {timezone: false});
        },
    });

    var FieldTimePicker = FieldDate.extend({
        supportedFieldTypes: ['float'],
//        supportedFieldTypes: ['char'],
        floatTimeFormat: "HH:mm",

        init: function () {
            this._super.apply(this, arguments);
            this.originalValue = this.value;
            var defDate = null;
            if (!!this.value) {
                if (this.value.contains(':')) {
                    defDate = new moment(this.value, this.floatTimeFormat);
                } else {
//                    defDate = new moment(this._formatValue(this.value),
//                        this.floatTimeFormat);
                    var formattedValue = field_utils.format.float_time(this.value)
                    defDate = new moment(formattedValue,
                        this.floatTimeFormat);
                    this.value = `${this.pad(defDate.hour(), 2)}:${this.pad(defDate.minute(), 2)}`;
                }
                // console.log('init 1', this.originalValue, 'new: ', this.value, defDate, defDate.hour(), defDate.minute())
            }
            // Hard-Coded Format: Field is an float and conversion only accept
            // HH:mm format
            this.datepickerOptions = _.extend(this.datepickerOptions, {
                format: this.floatTimeFormat,
                defaultDate: defDate && defDate.isValid()
                    ? defDate : new moment(),
                toolbarPlacement: "bottom",
//                closeText: "Ok",
//                showButtonPanel: true,
//                onSelect:function(event){
//                      event.preventDefault();
//                      // blah blah blah
//                  }
            });
        },
        pad: function (num, size) {
            var s = "000" + num;
            return s.substr(s.length-size);
        },
        _isSameValue: function (value) {
            return value === this.value;
        },

        _makeDatePicker: function () {
            return new TimeWidget(this, this.datepickerOptions);
        },

        _formatValue: function (value) {
            //console.log('format value', value)
            return value;  // field_utils.format.datetime(value, null, {timezone: false});
//            return field_utils.format.float_time(value);
        },

        _parseValue: function (value) {
            //console.log('parse value', value)
            return value;  // field_utils.format.datetime(value, null, {timezone: false});
//            return field_utils.parse.float_time(value);
        },
    });

    field_registry.add('kg_time_picker', FieldTimePicker);
    return {
        TimeWidget: TimeWidget,
        FieldTimePicker: FieldTimePicker,
    };
});
