odoo.define('kg_report_base.KgFieldReportView', function(require) {
"use strict";

var field_registry = require('web.field_registry');
var AbstractField = require('web.AbstractField');
var kgReportProcessor = require('kg_report_base.report_processor');

//var FormController = require('web.FormController');
//
//FormController.include({
//    _update: function () {
//        var _super_update = this._super.apply(this, arguments);
//        this.trigger('view_updated');
//        return _super_update;
//    },
//});

var KgFieldReportView = AbstractField.extend({
    template: 'KgFieldReportViewTemplate',
    className: 'oe_form_field_kg_report_viewer',
    init: function() {
        this._super.apply(this, arguments);
        this.showReport = false;
        this.rptJsonData = null;
        this.rptName = null;
        this.rptProcessCount = 1;
    },
    start: function() {
        // called after rendering finished
        // https://www.odoo.com/documentation/11.0/reference/javascript_reference.html
        var self = this;
        // value is field value pass to this fieldView
        // console.log('KgFieldReportView - start: ', self.value)
        var startObj = this._super();
        // console.log('KgFieldReportView - start - done');
        return startObj;
    },
//    events: {
//        'click .btn': '_button_clicked',
//    },
    _button_clicked: function(e) {
        // this._setValue(parseInt(jQuery(e.target).attr('data-id')));
    },
    _render: function() {
        // this.renderElement();
        var self = this;
        kgReportShow = false
        var reportData = this.value
        // load stimulsoft report
        var reportProcessor = new kgReportProcessor()
        var divId = "kg_report_view_content"
        var showReport = reportProcessor.processReport(reportData)

        // bug, report penuh 1 halaman, belum ketemu solusinya
        // sementara render melalui javascript script di template:
        //      \local\kg_report_base\static\src\xml\report-view.xml
        kgReportViewerField = reportProcessor.kgReportViewer

        self.renderElement();
        // reportProcessor.renderKgReport(showReport, divId)
    },
});

field_registry.add('kg-report-view-field', KgFieldReportView);

return {
    KgFieldReportView: KgFieldReportView,
};

});