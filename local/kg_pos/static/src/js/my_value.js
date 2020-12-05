odoo.define('kg_pos.my_value', function(require) {
    'use_strict'

    var models = require('point_of_sale.models')
    var screens = require('point_of_sale.screens')
    var gui = require('point_of_sale.gui')
    var popups = require('point_of_sale.popups')
    var core = require('web.core')
    var rpc = require('web.rpc')

    var _t = core._t
    
    var _super_order = models.Order.prototype
    models.Order = models.Order.extend({
        initialize: function() {
            _super_order.initialize.apply(this, arguments)

            this.my_value_id = this.my_value_id
            this.my_value_name = this.my_value_name
            this.my_value_data = this.my_value_data
            this.my_value_list = this.my_value_list
            this.my_value_points = this.my_value_points
            this.my_value_points_used = this.my_value_points_used

            // store/track API Earning status
            this.my_value_earn_status = this.my_value_earn_status || false
            this.my_value_earn_amount = this.my_value_earn_amount || 0
            this.my_value_earn_point = this.my_value_earn_point || 0
            this.my_value_earn_error_desc = this.my_value_earn_error_desc || false
            this.my_value_earn_send_date = this.my_value_earn_send_date

            this.save_to_db()
        },
        export_as_JSON: function() {
            var json = _super_order.export_as_JSON.apply(this, arguments)

            json.my_value_id = this.my_value_id
            json.my_value_name = this.my_value_name
            json.my_value_data = this.my_value_data
            json.my_value_list = this.my_value_list
            json.my_value_points = this.my_value_points
            json.my_value_points_used = this.my_value_points_used

            json.my_value_earn_status = this.my_value_earn_status
            json.my_value_earn_amount = this.my_value_earn_amount
            json.my_value_earn_point = this.my_value_earn_point
            json.my_value_earn_error_desc = this.my_value_earn_error_desc
            json.my_value_earn_send_date = this.my_value_earn_send_date


            return json
        },
        init_from_JSON: function(json) {
            _super_order.init_from_JSON.apply(this, arguments)

            this.my_value_id = json.my_value_id
            this.my_value_name = json.my_value_name
            this.my_value_data = json.my_value_data
            this.my_value_list = json.my_value_list
            this.my_value_points = json.my_value_points
            this.my_value_points_used = json.my_value_points_used

            this.my_value_earn_status = json.my_value_earn_status
            this.my_value_earn_amount = json.my_value_earn_amount
            this.my_value_earn_point = json.my_value_earn_point
            this.my_value_earn_error_desc = json.my_value_earn_error_desc
            this.my_value_earn_send_date = json.my_value_earn_send_date

        
        },
        export_for_printing: function() {
            var json = _super_order.export_for_printing.apply(this, arguments)

            json.my_value_id = this.my_value_id
            json.my_value_name = this.my_value_name
            json.my_value_data = this.my_value_data
            json.my_value_list = this.my_value_list
            json.my_value_points = this.my_value_points
            json.my_value_points_used = this.my_value_points_used

            json.my_value_earn_status = this.my_value_earn_status
            json.my_value_earn_amount = this.my_value_earn_amount
            json.my_value_earn_point = this.my_value_earn_point
            json.my_value_earn_error_desc = this.my_value_earn_error_desc
            json.my_value_earn_send_date = this.my_value_earn_send_date

            return json
        },
        set_my_value_data: function(my_value_id, my_value_name, my_value_data, my_value_list) {
            this.my_value_id = my_value_id
            this.my_value_name = my_value_name
            this.my_value_data = my_value_data
            this.my_value_list = my_value_list
            
            this.trigger('change')
        },
        get_my_value_data: function() {
            return {
                my_value_id: this.my_value_id,
                my_value_name: this.my_value_name,
                my_value_data: this.my_value_data,
                my_value_list: this.my_value_list,
            }
        },
        set_my_value_points: function(my_value_points, my_value_points_used) {
            this.my_value_points = my_value_points
            this.my_value_points_used = my_value_points_used

            this.trigger('change')
        },
        get_my_value_points: function() {
            return {
                my_value_points: this.my_value_points,
                my_value_points_used: this.my_value_points_used,
            }
        },
        set_my_value_redeem_response: function(response) {
            this.my_value_redeem_response = response
            this.my_value_redeem_response_code = response ? response.code : 0
            this.trigger('change')
        },
        set_my_value_earn_response: function(response, amount=0,
                my_value_outlet_id=false, total_earn_point=0) {
            this.my_value_earn_response = response
            var status = 'N'  // false/null = Not applicable, Y = success, E = error
            var errorDesc = false
            var sendDate = false
            if (amount === undefined) {
                amount = 0
            }

            var total_earn_point = 0

            this.my_value_earn_response_code = response ? response.code : 0
            if (response && amount > 0) {
                sendDate = (new Date()).toISOString()
                var success_code = [200, 201]
                if (success_code.includes(response.code)) {
                    status = 'Y'
                    total_earn_point = response.total_earn_point
                } else {
                    // if error because of my_value_outlet_id is empty/false, set status = N == Not Applicable
                    status = !my_value_outlet_id ? 'N' : 'E'
                    if (response && response.response) {
                        if (response.response.Message) {
                            errorDesc = response.response.Message
                        }
                        else  {
                            errorDesc = JSON.stringify(response.response)
                        }
                    } else if (response) {
                        errorDesc = JSON.stringify(response)
                    }
                    errorDesc = errorDesc.substring(0, 250)
                }
            }
            this.my_value_earn_point = total_earn_point  // earning amount in point
            this.my_value_earn_amount = amount // earning amount in currency
            this.my_value_earn_status = status
            this.my_value_earn_error_desc = errorDesc
            this.my_value_earn_send_date = sendDate
            this.trigger('change')
        },
        set_redeem_transaction_check: function(condition) {
            this.redeem_transaction_check = condition
        },
    })
    

    var MyValueWidget = popups.extend({
        template: 'MyValueWidget',
        show: function(options) {
            var self = this

            order = this.pos.get_order()

            if (!order.pos.config.my_value_outlet_id) {
                 order.pos.gui.show_popup('error',{
                     'title':_t('MyValue Disabled'),
                     'body': _t('Outlet ID is not defined in POS Config. MyValue is disabled.'),
                 });
                 return
            }

            options = options || {}

            this._super(options)

            if (order.my_value_data) {
                self.my_value_id = order.my_value_id
                self.my_value_name = order.my_value_name
                self.renderElement()
                self.$('#my-value-customer-div').removeClass('oe_hidden')
                $('#apply-my-value').removeClass('oe_hidden')

                $('#my-value-customer').change(function() {
                    if ($('#my-value-customer').val() === '') {
                        $('#apply-my-value').addClass('oe_hidden')
                    }
                    else {
                        let myValueAttr = $('#my-value-customer option:selected').html()
                        let myValueName = myValueAttr.split('--')

                        console.log('namanya', myValueName[0])

                        $('#apply-my-value').removeClass('oe_hidden')
                    }
                })
            }

            this.$('#my-value-id').keypress(function() {
                $('#my-value-customer-div').addClass('oe_hidden')
                $('#apply-my-value').addClass('oe_hidden')
            })

            this.$('#my-value-id').keyup(function() {
                $('#my-value-customer-div').addClass('oe_hidden')
                $('#apply-my-value').addClass('oe_hidden')
            })

            this.$('#verify-my-value').click(function(event){
                self.search_myvalue_id(event, self)
            })
        },
        search_myvalue_id: function(event, data) {
            var myvalue_id = $('#my-value-id').val()
            var myvalue_customer_div = $('#my-value-customer-div')
            var not_found_customer = $('#customer-not-found')
            var customer_list = $('#my-value-customer')
            var apply_my_value = $('#apply-my-value')
            var exceptionError = $('#myvalue-exception-error')

            var order = data.pos.get_order()
            order.my_value_found = false

            myvalue_customer_div.addClass('oe_hidden')
            exceptionError.addClass('oe_hidden')
            not_found_customer.addClass('oe_hidden')

            if (myvalue_id) {
                rpc.query({
                    model: 'pos.helpers',
                    method: 'get_myvalue_customer',
                    args: [myvalue_id],
                }).then(function(response) {
                    console.log('response get member', response)
                    if (response.error) {
                        exceptionError.html(response.error.message)
                        exceptionError.removeClass('oe_hidden')
                        return
                    }
                    var options = []
                    if (response.Data && response.Data.length > 0) {
                        for (var i = 0; i < response.Data.length; i++) {
                            var my_value = response.Data[i]
                            options.push(
                                `<option value=${my_value.PersonSNO}>` +
                                    `${my_value.FullName}` + ` -- (` + `${my_value.ValueID}` +
                                    `) -- ` + `${my_value.PersonSNO}` +
                                    '</option>'
                            )
                        }
                        
                        order.set_my_value_data(null, null, null, response.Data)
                        order.my_value_found = true

                        myvalue_customer_div.removeClass('oe_hidden')
                        customer_list.empty().append(options)
                        
                        if (options !== []) {
                            apply_my_value.removeClass('oe_hidden')
                        }
                        else {
                            apply_my_value.addClass('oe_hidden')
                        }

                        // $('#my-value-customer').change(function() {
                        //     if ($('#my-value-customer').val() === '') {
                        //         apply_my_value.addClass('oe_hidden')
                        //     }
                        //     else {
                        //         apply_my_value.removeClass('oe_hidden')
                        //     }
                        // })
                    }
                    else {
                        order.my_value_found = false
                        apply_my_value.addClass('oe_hidden')
                        not_found_customer.removeClass('oe_hidden')
                    }
                }, (ex) => {
                    // Exception/error (jika return dari backend odoo != 200)
                    exceptionError.html(ex.data.arguments[0])
                    exceptionError.removeClass('oe_hidden')
                    // console.log ('exception', ex.data.message, ex)
                })
            }
            else {
                apply_my_value.removeClass('oe_hidden')
                // data.pos.gui.show_popup('error',{
                //     'title':_t('MyValue Error'),
                //     'body': _t('You must input MyValue ID.'),
                // });
            }

        },
        click_confirm: function(event) {
            var my_value_id = this.$('#my-value-id').val()
            var my_value_customer_selected = this.$('#my-value-customer').val()
            var order = this.pos.get_order()
            var selected_my_value_data = null
            var my_value_name = null
            console.log('selected myvalue', my_value_id, my_value_customer_selected)
            if (my_value_id === '' || my_value_customer_selected === '') {
                order.set_my_value_data(false, false, false, false)
                this.gui.close_popup()
            }

            else {
                if (order.my_value_list.length > 0) {
                    for (var i = 0; i < order.my_value_list.length; i++) {
                        if (order.my_value_list[i].PersonSNO == parseInt(my_value_customer_selected)) {
                            selected_my_value_data = order.my_value_list[i]
                            my_value_name = order.my_value_list[i].FullName
                        }
                    }
                }
                console.log('selected', selected_my_value_data)
                
                order.set_my_value_data(my_value_id, my_value_name, selected_my_value_data, order.get_my_value_data().my_value_list)
                console.log('selected', my_value_name)
                this.gui.close_popup()
            }
        }
        
    })

    gui.define_popup({ name: 'my-value', widget: MyValueWidget })

    var MyValueButton = screens.ActionButtonWidget.extend({
        template: 'MyValueButton',
        button_click: function() {
            var self = this
            this.gui.show_popup('my-value', {
                title: _t('MyValue ID'),
                cheap: true,
            })
        },
        renderElement: function() {
            var self = this
            this._super()
            
        },
    })

    screens.define_action_button({
        name: 'my-value-button',
        widget: MyValueButton,
    })

    var MyValuePaymentWidget = popups.extend({
        template: 'MyValuePaymentWidget',
        show: function(options) {
            var self = this
            order = this.pos.get_order()
            options = options || {}

            this._super(options)
            
            if (order.my_value_data) {
                this.search_myvalue_points()
            }

            this.$('#my-value-points-used').keyup(function() { 
                input_points = $('#my-value-points-used').val().toLowerCase()
                if (input_points !== '') {
                    if (input_points.match(/[a-z]/g)) {
                        $('#my-value-points-used').val('')
                    }
                    else {
                        points_used = $('#my-value-points-used').val()
                        fixed_points_used = self.numberWithCommas(points_used)
                        $('#my-value-points-used').empty().val(fixed_points_used)
                    }
                }
            })
        },
        search_myvalue_points: function() {
            var self = this
            var order = this.pos.get_order() 
            var my_value_selected_data = order.get_my_value_data().my_value_data
            this.enable_keypress = true
            
            if (my_value_selected_data) {
                rpc.query({
                    model: 'pos.helpers',
                    method: 'get_myvalue_customer_with_point',
                    args: [my_value_selected_data],
                }).then(function(response) {
                    var total_points = 0.0
                    console.log('response get point', response)
                    if (response.Data) {
                        total_points = response.Data.TotalPoint
                        order.set_my_value_points(total_points, 0.0)
                        
                        $('#my-value-points').val(order.my_value_points.toLocaleString().replace(/,/g, '.') || '')
                    }               
                })
            }
            else {
                this.pos.gui.show_popup('error',{
                    'title':_t('MyValue Error'),
                    'body': _t('You must input MyValue ID.'),
                });
            }

        },
        numberWithCommas:function (number) {
            var parts = number;
            if (parts.match(/\./g)) {
                process_parts = parts.replace(/\./g,'')
                parts = process_parts
            }
            parts = parts.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
            return parts;
        }
    })

    gui.define_popup({ name: 'my-value-payment', widget: MyValuePaymentWidget })

})
