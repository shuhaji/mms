odoo.define('custom.search_filter', function (require) {
    var inputInt = require('web.inputInt');
    var search_filters = require('web.search_filters');
    search_filters.DateTime.include({
        _create_new_integer_widget: function (name) {
            this[name] = new (this._get_widget_integer_class())(this);
            return this[name].appendTo(this.$el).then((function () {
            }).bind(this));
        },
        _get_widget_integer_class: function () {
            return inputInt.InputInt;
        },
        get_value_number: function (name) {
            if (name === "add") {
                var value = this["value_0"].getDate_Add();//lay gia tri thoi gian hien tai cong them mot doi so
                return value;
            } else if (name === "sub") {
                var value = this["value_0"].getDate_Sub();//lay gia tri thoi gian hien tai tru them mot doi so
                return value;
            }
        },
        //hide datewidget
        _hide_datewidget: function () {
            this.datewidget_0.do_hide();
            if(!this.datewidget_97){
                this._create_new_widget("datewidget_97");
                this.datewidget_97.do_hide();
            }else{
                this.datewidget_97.do_hide();
            }
        },
        //hide input integer
        _hide_input_integer: function () {
            this["value_0"].do_hide_input();
        },
        //show input integer
        _show_input_integer: function () {
            this["value_0"].do_show_input();
        }
    });
});