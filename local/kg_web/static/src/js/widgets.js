odoo.define('web_many2many_button.form_widgets', function (require) {
	"use strict";

	var core = require('web.core');
	var _t = core._t;
	var rpc = require('web.rpc');
	var field_registry = require('web.field_registry');
	var FieldMany2Many = field_registry.get('many2many');
    var dialogs = require('web.view_dialogs');

	var Many2ManyButton = FieldMany2Many.extend({
		template: 'Many2ManyButton',
		//button click
		events: {
			"click .cf_button_add": "action_add_records",
		},
		init: function () {
            this._super.apply(this, arguments);
            if (this.mode === 'readonly') {
    		    this.effective_readonly = true
    		} else {
    		    this.effective_readonly = false
    		}
    		// console.log('edit mode: ', this.mode, this.effective_readonly)
        },
		start: function() 
	    {
			var self=this;
	    	this._super.apply(this, arguments);
		},
		_render: function () {
		    if (!this.view) {
                return this._super();
            }
    		this.view.arch.tag = 'button_only'
    		var return_value = this._super.apply(this, arguments);
    		this.$('.cf_button_add_many2many_button_only').toggle(!this.effective_readonly)
    		return return_value
		},
		action_add_records: function(ev) {
		    var self = this;
		    if (!!ev) {
                ev.stopPropagation();
		    }

            //console.log('one2many_multiselect', this.field.relation, this.value, this.value.res_ids)
            //console.log('one2many_multiselect', this.record)
            var domain = this.record.getDomain({fieldName: this.name});

            new dialogs.SelectCreateDialog(this, {
                res_model: this.field.relation,
                domain: domain.concat(["!", ["id", "in", this.value.res_ids]]),
                context: this.record.getContext(this.recordParams),
                title: _t("Add: ") + this.string,
                no_create: this.nodeOptions.no_create || !this.activeActions.create,
                fields_view: this.attrs.views.form,
                on_selected: function (records) {
                    var resIDs = _.pluck(records, 'id');
                    //console.log('one2many_multiselect', resIDs)
                    var newIDs = _.difference(resIDs, self.value.res_ids);
                    if (newIDs.length) {
                        var values = _.map(newIDs, function (id) {
                            return {id: id};
                        });
                        self._setValue({
                            operation: 'ADD_M2M',
                            ids: values,
                        });
                    }
                }
            }).open();
		},
	});

	// you can use <field name="Many2many_ids" widget="many2many_button"> for call this widget
	field_registry.add('many2many_button', Many2ManyButton);
});
