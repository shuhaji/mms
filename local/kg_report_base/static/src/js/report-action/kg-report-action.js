// © 2017 Creu Blanca
// License AGPL-3.0 or later (https://www.gnuorg/licenses/agpl.html).
odoo.define('kg_report_base.report_action', function(require){
'use strict';

//var Widget = require('web.Widget');
//var widgetRegistry = require('web.widget_registry');
//var ControlPanelMixin = require('web.ControlPanelMixin');
var reportClientAction = require('report.client_action');
var core = require('web.core');
var ControlPanelMixin = require('web.ControlPanelMixin');
var session = require('web.session');
var kgReportProcessor = require('kg_report_base.report_processor');

var QWeb = core.qweb;

var kgReportClientAction = reportClientAction.extend(ControlPanelMixin, {
    template: 'report.client_action_kg_report_template',

    init: function (parent, action, options) {
        var self = this;
        this._super.apply(this, arguments);
        this.report_type = options.report_type;
        if (core.debug && window.console) {
            console.log('report-action -- options:', options)
        }
        self.report_url = ""
        self.docIds = options.docIds
        self.activeModel = options.active_model
    },
    start: function () {
        var self = this;
        kgReportShow = false;
        if (!!self.report_type && self.report_type === 'mrt') {
            // this.set('title', this.title);
            return $.when(this._super.apply(this, arguments), session.is_bound).then(function () {
            // return session.is_bound.then(function () {
                self._start_render_buttons()
                self._loadReport()
            });
        } else {
            self._super.apply(self, arguments);
        }
    },
    _loadReport: function() {
        var self = this;
        // handle mrt report
        kgReportShow = false;
        var reportData = false
        var reportModel = this.report_name
        // get json data from report rpc method
        if (core.debug && window.console) {
            console.log('report-action -- load report with params:',
                reportModel, self.activeModel, self.docIds, self.data)
        }
        this._rpc({
                model: reportModel,
                method: 'get_report_data',
                args: [self.docIds, self.data, self.activeModel],
            })
            .then(function(data) {
                if (core.debug && window.console) {
                    console.log('report-action -- response data:',
                        data)
                }
                reportData = data
                // load stimulsoft report
                var reportProcessor = new kgReportProcessor()
                var divId = "kg_report_view_content"
                var showReport = reportProcessor.processReport(reportData)
                self.kgReport = reportProcessor.kgReport
                reportProcessor.renderKgReport(showReport, divId)
            });
    },
    _showPrintDialog: function() {
        if (!!kgReportShow && !!this.kgReport) {
            // kgReport.render()
            this.kgReport.print()
        }
    },
    _start_render_buttons: function() {
        var self = this

//        // TODO: this code not working yet...
//        self.$buttons = $(QWeb.render('report.client_action_kg_report_action.ControlButtons', {}));
//        self.$buttons.on('click', '.o_report_edit', self.on_click_edit);
//        self.$buttons.on('click', '.o_report_print', self.on_click_print);
//        self.$buttons.on('click', '.o_report_save', self.on_click_save);
//        self.$buttons.on('click', '.o_report_discard', self.on_click_discard);
//
//        // TODO: attach back button to an event!
//        self.$buttons.on('click', '.o_report_back_cancel', self.on_click_back_cancel);
//
//        self._update_control_panel();

        this.$('.o_report_back_cancel').click(function(){
            self.on_click_back_cancel()
        });
        this.$('.o_report_reload').click(function(){
            kgVersionDummy = (new Date()).getTime();
            self._loadReport()
        });
        this.$('.o_report_showPrint').click(function(){
            self._showPrintDialog()
        });
    },
    _update_control_panel_buttons: function () {
        this._super();
        if (!!this.report_type && this.report_type === 'mrt') {
            // hide print button
            this.$buttons.filter('div.o_report_no_edit_mode').toggle(false);
        }
    },
    on_click_back_cancel: function() {
        window.history.back();
    },
    on_click_print: function() {
        var self = this;
        if (!!self.report_type && self.report_type === 'mrt' && !!kgReportShow) {
            // override print , print stimulsoft report
            console.log('print report - direct')
            // self.kgReport.render()
            self.kgReport.print()
        } else {
            // print default
            this._super.apply(this, arguments);
        }
    }
});

core.action_registry.add('report.client_action_kg_report', kgReportClientAction);

return kgReportClientAction;
});
