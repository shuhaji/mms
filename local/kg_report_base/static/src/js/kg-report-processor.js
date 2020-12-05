odoo.define('kg_report_base.report_processor', function(require){
'use strict';

var core = require('web.core');
var mixins = require('web.mixins');
var ServicesMixin = require('web.ServicesMixin');

var KgReportProcessor = core.Class.extend(mixins.PropertiesMixin, ServicesMixin, {

    renderKgReport: function(showReport, divId) {
        if (core.debug && window.console) {
            console.log('report render: show?', kgReportShow, divId)
        }
        if (!!showReport && !!this.kgReportViewer) {
            var divIdForReport = !!divId ? divId : "kg_report_view_content"
            // render report to html
            this.kgReportViewer.renderHtml(divIdForReport);
            // bug, report penuh 1 halaman, belum ketemu solusinya
            // sementara render melalui javascript script di template:
            //      \local\kg_report_base\static\src\xml\report-view.xml
        }
    },
    processReport: function(value) {
        if (core.debug && window.console) {
            console.log('report processor: param value', value)
        }
        if (!value) {
            return false
        }
        var reportData = JSON.parse(value);
        if (core.debug && window.console) {
            console.log('report processor: report data (json) ', reportData)
        }
        if (!reportData) {
            // this.$el.html('');
            if (core.debug && window.console) {
                console.log('report processor: json data empty')
            }
            return false;
        }

        this.rptJsonData = reportData.json;
        this.rptName = reportData.reportName;
        this.variables = reportData.variables;

        // console.log('KgFieldReportView - _render - data:', kgReportShow, this.rptName);

        this.rptProcessCount += 1;

        Stimulsoft.Base.StiLicense.key = "6vJhGtLLLz2GNviWmUTrhSqnOItdDwjBylQzQcAOiHl+aLYI6fTAUqPi9nGZkVXg961FDINa8yEaEZOLLPaaqnAhD6" +
            "SXopCAiI1pG0O1oI3NaaWscuiyTB8FydXCZgo8jqxkDP8RhgXfvrL1CHBw9ivOcnsGExrvF8Q3+D4iD4B2LPa6wnc8" +
            "usZfTXG4BHiTKgfeya5RVdE66/3V6kPAN91nx+osA0cecVRUjrB6kQmQmV4P0vrcn1VHlaayBV3vlqvBH8Vh9akC5x" +
            "LpS/Jo+LhV7KfIJHnV0rdoyU27e/F3pBIEoD7+pMGtraau/RcihdOZCsN3q5JBvq9cm+nK2d1L1wr+hJiGZDM23she" +
            "9dePEOAkPdZp39xrVpsaOO9iWvJNFbLnaPngT0Z/LMv6W7fDHoRXOPUh+6Jdbim7+rEavKMRSr+feMFPvq8iReedyL" +
            "WegqxDJvUDUPu0LP2LmV7JDGG7klqppplpff9XGFViCOXvB9JyAcy3BjpzK0JmPvxCDia+kAOIx1XdFENyz3E7ayqC" +
            "4cxESDb+0dMQ9dNm+owY6ub9b/b28GoH9RdY";

        this.kgReport = new Stimulsoft.Report.StiReport();
        this.kgReport.loadFile(this.rptName);
        // console.log('variables: ', kgReport.dictionary.variables);
        this.kgReport.dictionary.databases.clear();

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

        var dataSet = new Stimulsoft.System.Data.DataSet("data");
        // Load JSON data file from specified URL to the DataSet object
        //dataSet.readJsonFile("/DataJSON.json");
        dataSet.readJson(this.rptJsonData);
        //report.regData("root", "root", dataSet);
        this.kgReport.regData("data", "", dataSet);
        if (!!reportData.json2) {
            var dataSet2 = new Stimulsoft.System.Data.DataSet("data2");
            dataSet2.readJson(reportData.json2);
            this.kgReport.regData("data2", "", dataSet2);
        }
        if (!!reportData.json3) {
            var dataSet3 = new Stimulsoft.System.Data.DataSet("data3");
            dataSet3.readJson(reportData.json3);
            this.kgReport.regData("data3", "", dataSet3);
        }

        // Define report viewer
        this.kgReportViewer = new Stimulsoft.Viewer.StiViewer(null, "StiViewer", false);
        this.kgReportViewer.report = this.kgReport;
        kgReportShow = true;
        if (core.debug && window.console) {
            console.log('report ready')
        }
        // reset moment (datetime) language to default en (bug datepicker show strange character after report viewer)
         moment.locale('en')
        return true
    },
    /**
     * Destroys the current object, also destroys all its children before destroying itself.
     */
    destroy: function () {
        _.each(this.getChildren(), function (el) {
            el.destroy();
        });
        if(this.$el) {
            this.$el.remove();
        }
        mixins.PropertiesMixin.destroy.call(this);
    },
});

return KgReportProcessor;
});
