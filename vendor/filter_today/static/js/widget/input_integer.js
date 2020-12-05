odoo.define('web.inputInt', function (require) {
    "use strict";
    var Widget = require('web.Widget');
    var InputInt = Widget.extend({
        template: 'InputInt',
        events: {
            'keyup .o_input_widget_number': function (e) {
                e.preventDefault();
                var val = $('.o_input_widget_number').val();
                $('.o_input_widget_number').val(val);
            },
            'change .o_input_widget_number': 'changeValue'
        },
        init: function (parent, title, text, sticky) {
            this._super.apply(this, arguments);
        },
        start: function () {
            this._super.apply(this, arguments);
        },
        changeValue: function () {
            this.trigger("value_changed_domain");
            var value = $(".o_input_widget_number").val();
            $(".o_input_widget_number").attr("placeholder" , value);
        },
        setValuePlaceholder: function (name) {
            $(".o_input_widget_number").val(name);
        },
        getValueNumber: function () {
            try {
                var val = $('.o_input_widget_number').val();
                if (val >= 0) {
                    var val = $('.o_input_widget_number').val();
                    return parseInt(val);
                }
            } catch (e) {
                console.log("error");
                return "";
            }
        },
        _addDays: function (dateObj, numDays) {
            dateObj.setDate(dateObj.getDate() + numDays);
            return dateObj;
        },
        _subDays: function (dateObj, numDays) {
            dateObj.setDate(dateObj.getDate() - numDays);
            return dateObj;
        },
        getDate_Add: function () {
            var val = this.getValueNumber();
            //convert moment
            return moment(this._addDays(new Date(), val));
        },
        getDate_Sub: function () {
            var val = this.getValueNumber();
            //convert moment
            return moment(this._subDays(new Date(), val));
        },
        getDateNoMoment_Add: function () {
            var val = this.getValueNumber();
            //convert moment
            return (this._addDays(new Date(), val));
        },
        getDateNoMoment_Sub: function () {
            var val = this.getValueNumber();
            //convert moment
            return (this._subDays(new Date(), val));
        },
        //hide and show input integer
        do_hide_input: function () {
            $('.o_input_widget_number').hide();
        },
        do_show_input: function () {
            $('.o_input_widget_number').show()
        },
        //end
        destroy: function (animate) {
        },
    });
    return {
        InputInt: InputInt
    };

});
