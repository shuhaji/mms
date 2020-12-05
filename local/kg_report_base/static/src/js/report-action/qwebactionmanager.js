// © 2017 Creu Blanca
// License AGPL-3.0 or later (https://www.gnuorg/licenses/agpl.html).
odoo.define('kg_report_base.report_action_manager', function(require){
'use strict';

var core = require('web.core');
var ActionManager= require('web.ActionManager');
var crash_manager = require('web.crash_manager');
var framework = require('web.framework');

ActionManager.include({
    ir_actions_report: function (action, options){
        var self = this;
        var cloned_action = _.clone(action);
        if (cloned_action.report_type === 'mrt') {
            var report_mrt_url = 'report/mrt/' + cloned_action.report_name;
            var docIds = ""
            if (_.isUndefined(cloned_action.data) ||
                _.isNull(cloned_action.data) ||
                (_.isObject(cloned_action.data) && _.isEmpty(cloned_action.data)))
            {
                if(cloned_action.context.active_ids) {
                    report_mrt_url += '/' + cloned_action.context.active_ids.join(',');
                    docIds = cloned_action.context.active_ids.join(',')
                }
            } else {
                report_mrt_url += '?options=' + encodeURIComponent(JSON.stringify(cloned_action.data));
                report_mrt_url += '&context=' + encodeURIComponent(JSON.stringify(cloned_action.context));
            }
            if (core.debug && window.console) {
                console.log('report-mrt-report_urls', report_mrt_url)
                console.log('report-mrt-cloned_action', cloned_action)
            }
            var client_action_options = _.extend({}, options, {
                report_url: report_mrt_url,
                report_name: action.report_name,
                report_file: action.report_file,
                report_type: cloned_action.report_type,
                data: action.data,
                docIds: docIds,
                active_model: cloned_action.model,
                context: action.context,
                name: action.name,
                display_name: action.display_name,
            });
            if (core.debug && window.console) {
                console.log('report-mrt-options', client_action_options)
            }
            return this.do_action('report.client_action_kg_report', client_action_options);
        }
        return self._super(action, options);
    }
});
});
