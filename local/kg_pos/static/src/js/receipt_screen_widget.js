odoo.define('kg_pos.receipt_screen_widget_report_mrt', function(require) {
    'use_strict'

var models = require('point_of_sale.models')
var screens = require('point_of_sale.screens')
var kgReportProcessor = require('kg_report_base.report_processor');
var rpc = require('web.rpc')

screens.ReceiptScreenWidget.include({
    render_receipt: function() {
        var self = this
        kgReportShow = false
        this.initiateKgReport()

        // render report (template PosTicket)
        this._super()
        // this.$('.pos-receipt-container').html(QWeb.render('PosTicket', this.get_receipt_render_env()));

        this.renderKgReport()

        if (self.pos.debug) {
            console.log('render-receipt-pos-receipt-screen', self.$('#reload_report_button'))
        }
        self.$('#reload_report_button').click(function(){
            kgVersionDummy = (new Date()).getTime();
            self.initiateKgReport()
            if (self.pos.debug) {
                console.log('report data', JSON.stringify(self.rptJsonData))
                }
            self.renderKgReport()
        });
//        self.$('#reload_report_button2').click(function(){
//            self.testReloadFromRpc()
//        })
    },
    renderKgReport: function() {
        if (!!kgReportShow && !!this.kgReportViewer) {
            this.kgReportViewer.renderHtml("kg_report_view_pos_bill_content");
        }
    },
//    handle_auto_print: function() {
//        if (this.should_auto_print()) {
//            this.print();
//            if (this.should_close_immediately()){
//                this.click_next();
//            }
//        } else {
//            this.lock_screen(false);
//        }
//    },
    print: function() {
        if (!!kgReportShow && !!this.kgReport) {
            // override print , print stimulsoft report
            console.log('print report - direct')
            this.kgReport.render()
            this.kgReport.print()
        } else {
            // load default xml
            this._super()
        }
    },
    get_receipt_json_data: function() {
        kgReportShow = false
        var widget = this
        var company = this.pos.company
        var shop    = this.pos.shop;
        var order = this.pos.get_order()
        var order_totals = order.get_all_order_totals()
        var order_lines = []
        var dummyOrderId = (new Date()).getTime()

        var pos_order_lines = order.get_orderlines()
        if (pos_order_lines.length) {
            pos_order_lines.forEach(function(line) {
                var line_all_prices = line.get_all_prices()
                var product = line.get_product()
                pos_line = {
                    order_id: dummyOrderId,
                    quantity: line.quantity,
                    displayName: line.get_display_name(),
                    note: line.note,
                    priceWithTax: line_all_prices.priceWithTax,
                    // Total After Discount Before Tax/Service = priceWithoutTax
                    priceWithoutTax: line_all_prices.priceWithoutTax,
                    tax: line_all_prices.tax,
                    //taxDetails: line_all_prices.taxDetails,
                    serviceAmount: line_all_prices.serviceAmount,
                    taxWithoutService: line_all_prices.taxWithoutService,
                    // Sub Total Line sebelum discount dan sebelum kena pajak/service
                    bruttoBeforeTax: line_all_prices.bruttoBeforeTax,
                    // Amount discount sebelum kena pajak/service
                    lineDiscAmountBeforeTax: line_all_prices.lineDiscAmountBeforeTax,
                    note: line.note,
                    main_category: line.get_product().main_category,
                    // custom code - end
                           
                    unit_name:          line.get_unit().name,
                    price:              line.get_unit_display_price(),
                    discount:           line.get_discount(),
                    product_name:       line.get_product().display_name,
                    product_name_wrapped: line.get_product().display_name, // line.generate_wrapped_product_name() ? line.generate_wrapped_product_name()[0] : "",
                    price_display :     line.get_display_price(),
                    product_description:      product.description ? product.description : "",
                    product_description_sale: product.description_sale ? product.description_sale : "",
               
                }
                order_lines.push(pos_line)
            })
        }
        var is_officer_check = false
        var is_department_expense = false
        var order_payment_lines = order.get_paymentlines()
        var payment_lines = []
        if (order_payment_lines.length > 0) {
            order_payment_lines.forEach(function(line) {
                payment_data = {
                    order_id: dummyOrderId,
                    name: line.name,
                    amount: line.get_new_amount(),
                    is_officer_check: line.cashregister.journal.is_officer_check,
                    is_department_expense: line.cashregister.journal.is_department_expense,
                }
                if (line.cashregister.journal.is_officer_check) {
                    is_officer_check = true
                    payment_data.name = "Employee: " + order.employee_id.name
                }
                if (line.cashregister.journal.is_department_expense) {
                    is_department_expense = true
                    payment_data.name = "Departement: " + order.department_id.name
                }
                payment_lines.push(payment_data)
            })
        } else {
            payment_lines.push({
                order_id: dummyOrderId,
                name: "Waiting for Payment",
                amount: order.get_new_total(),
                is_officer_check: false,
                is_department_expense: false
              })
        }
        var cashier = this.pos.get_cashier()

        // bug fix: stimulsoft 2019.3.6 cannot accept date isoformat with miliseconds like this:
        //      "2019-10-01T07:22:54.098Z"
        //  remove millisecond will fix this issue.
        //      valid format as of now: "2019-10-01T07:22:54Z"
        order.initialize_validation_date()
        // console.log('order', order)
        var validation_date = order.validation_date ? order.validation_date.toISOString().split('.')[0]+"Z" : ''

        var hide_service_tax = is_officer_check || is_department_expense
        return {
            orders: [{
                order_id: dummyOrderId,
                name: order.name,
                config_name: this.pos.config.name,
                table_name: this.pos.table ? "TBL    " +  this.pos.table.name : ""  ,
                cashier_name: cashier ? cashier.name : '',
                waiter_name: order.waiter ? order.waiter.name : '',
                is_hotel_guest: order.is_hotel_guest ? "I" : "O",
                customer_count: order.customer_count,
                "validation_date":  validation_date,
                hide_service_tax: hide_service_tax,
                print_counter: 0,
                "is_officer_check": is_officer_check,
			    "is_department_expense": is_department_expense,
			    currency_symbol: " ",

//                order_totals: {
                discount: order_totals.totalDiscAmountBeforeTax,
                sub_total: order.get_total_without_tax(),
                service: hide_service_tax ? 0 : order_totals.totalServiceAmount,
                tax: hide_service_tax ? 0 : order_totals.totalTaxWithoutService,
                total: order.get_new_total(),
                // total change/kembalian:
                change: order.get_change(),
//                    // Sub Total before discount and before tax/service
//                    totalBruttoBeforeTax: order_totals.totalBruttoBeforeTax,
//                     // Amount discount before tax/service
//                    totalDiscAmountBeforeTax: order_totals.totalDiscAmountBeforeTax,
//                    // discount amount (tax/services included)
//                    // totalDiscAmountWithTax: order.get_total_discount(),
//                    // sub Total after discount, before tax/service calculation (without tax/service)
//                    totalBeforeTax: order_totals.totalBeforeTax,
//                    // sub total after discount and tax/service:
//                    totalWithTax: order_totals.totalWithTax,
//                    totalServiceAmount: order_totals.totalServiceAmount,
//                    totalTaxWithoutService: order_totals.totalTaxWithoutService,
//                },
                order_lines: order_lines,
                payment_lines: payment_lines,
                company_name: company.name,
//                company: {
//                    email: company.email,
//                    website: company.website,
//                    company_registry: company.company_registry,
//                    contact_address: company.partner_id[1],
//                    vat: company.vat,
//                    vat_label: company.country && company.country.vat_label || '',
//                    phone: company.phone,
//                    // logo:  this.pos.company_logo_base64,
//                },
                shop_name: shop.name,
                currency_rounding: this.pos.currency.rounding
//                currency: this.pos.currency
            }]
        };
    },
    get_report_name: function() {
        // override this function to define other report that not from pos config receipt_bill_report_name
        return this.pos.config.receipt_bill_report_name
    },
    initiateKgReport: function() {
        this.rptJsonData = this.get_receipt_json_data()
        kgReportShow = true
        // console.log('pos.config', this.pos.config)
        var reportName = this.get_report_name()
        if (!reportName) {
            kgReportShow = false
            return false
        };
        // var timestamp = (new Date()).getTime();
        // kgVersionDummy = (new Date()).getTime(); --> see: custom/local/kg_report_base/static/src/js/kg-report-initial.js
        this.rptName = `/kg_pos/static/rpt/${reportName}?version=${kgVersionDummy}`;
        // this.rptName = `/kg_pos/static/rpt/${reportName}`;
        if (this.pos.debug) {
            console.log('report name: ', this.rptName)
        }
        // define variables
        this.defineReportVariables()

        var reportData = JSON.stringify({
            json: this.rptJsonData,
            reportName: this.rptName,
            variables: this.variables
        })
        // load stimulsoft report
        var reportProcessor = new kgReportProcessor()
        var divId = "kg_report_view_pos_bill_content"
        var showReport = reportProcessor.processReport(reportData)
        this.kgReport = reportProcessor.kgReport
        this.kgReportViewer = reportProcessor.kgReportViewer
        // reportProcessor.renderKgReport(showReport, divId)

//        // prepare stimulsoft mrt report objects
//        this.kgReport = new Stimulsoft.Report.StiReport();
//        this.kgReport.loadFile(this.rptName);
//        // console.log('variables: ', this.kgReport.dictionary.variables);
//        this.loadVariables()
//        this.kgReport.dictionary.databases.clear();
//        var dataSet = new Stimulsoft.System.Data.DataSet("data");
//        // Load JSON data file from specified URL to the DataSet object
//        //dataSet.readJsonFile("/DataJSON.json");
//        dataSet.readJson(this.rptJsonData);
//        this.kgReport.regData("data", "", dataSet);
//        // Define report viewer
//        var options = new Stimulsoft.Viewer.StiViewerOptions();
//        // options.appearance.scrollbarsMode = true;
//        options.toolbar.viewMode = Stimulsoft.Viewer.StiWebViewMode.Continuous;
//        // var viewer = new Stimulsoft.Viewer.StiViewer();
//        this.kgReportViewer = new Stimulsoft.Viewer.StiViewer(options, "StiViewer", false);
//        this.kgReportViewer.report = this.kgReport;
//        kgReportShow = true;
        // reset moment (datetime) language to default en (bug datepicker show strange character after report viewer)
        // moment.locale('en')
    },
    defineReportVariables: function() {
        this.variables = []
        var pathLogo = "/web/binary/company_logo"
        var company_id = this.pos.company.id
        // var timestamp = (new Date()).getTime();
        var logoUrlPath = `${pathLogo}?company=${company_id}&version=${kgVersionDummy}`;
        // var logoUrlPath = `${pathLogo}?company=${company_id}`;
        // console.log('report log', logoUrlPath)
        var logoVariable = {
            key: "LogoImage",
            value: logoUrlPath,
            is_image: true,
            format_value: 'url'
        }
        this.variables.push(logoVariable)
    },
    loadVariables: function() {
        // load variables
        if (!!this.variables && Array.isArray(this.variables)) {
            // kgReport.dictionary.variables.getByName("LogoImage").valueObject = new Stimulsoft.Base.Drawing.StiImageFromURL.loadImage("@ViewBag.HotelInfo.ImageURL");
            // kgReport.dictionary.variables.getByName("NameBill").valueObject = "Nama Abc";
            // kgReport.dictionary.variables.getByName("AddressBill1").valueObject = "Alamat 123";
            // kgReport.dictionary.variables.getByName("AddressBill2").valueObject = "Alamat 12323";
            this.variables.forEach((paramVar) => {
                var currentVariable = this.kgReport.dictionary.variables.getByName(paramVar.key)
                // console.log('report variable', paramVar, currentVariable)
                if (!!currentVariable) {
                    if (paramVar.is_image) {
                        if (paramVar.format_value === 'str') {
                            var image = new Stimulsoft.Base.Drawing.StiImageConverter.StringToImage(paramVar.value);
                        } else {
                            var image = new Stimulsoft.Base.Drawing.StiImageFromURL.loadImage(paramVar.value);
                        }
                        // console.log('image', paramVar.value, image);
                        currentVariable.valueObject = image
                    } else {
                        currentVariable.valueObject = paramVar.value
                    }
                }
            })
        }
    },
    renderElement: function() {
        var self = this;
//        if (self.pos.debug) {
//            console.log('render-element-pos-receipt-screen')
//        }
        this._super();
    },
    get_receipt_render_env: function() {
        var obj = this._super()
        obj.showKgReportViewer = kgReportShow
        return obj
    },
    testReloadFromRpc: function() {
        rpc.query({
            model: 'report.kg_report_action_pos_order_bill',
            method: 'get_report_data',
            args: [[285], null, 'pos.order'],
        })
        .then(function(data) {
            kgVersionDummy = (new Date()).getTime();
            if (self.pos.debug && window.console) {
                console.log('report-action -- response data:',
                    data)
            }
            reportData = data
            // load stimulsoft report
            var reportProcessor = new kgReportProcessor()
            var divId = "kg_report_view_pos_bill_content"
            var showReport = reportProcessor.processReport(reportData)
            self.kgReport = reportProcessor.kgReport
            self.kgReportViewer = reportProcessor.kgReportViewer
            self.renderKgReport()
            //reportProcessor.renderKgReport(showReport, divId)
        });
    }
})
});