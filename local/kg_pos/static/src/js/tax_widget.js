odoo.define('kg_pos.tax_widget', function (require) {
    "use strict";
    
    var AbstractField = require('web.AbstractField');
    var core = require('web.core');
    var field_registry = require('web.field_registry');
    var field_utils = require('web.field_utils');
    
    var QWeb = core.qweb;
    
    
    var ShowTaxLineWidget = AbstractField.extend({
        supportedFieldTypes: ['char'],
    
        //--------------------------------------------------------------------------
        // Public
        //--------------------------------------------------------------------------
    
        /**
         * @override
         * @returns {boolean}
         */
        isSet: function() {
            return true;
        },
    
        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------
    
        /**
         * @private
         * @override
         */
        _render: function() {
            var self = this;
            var info = JSON.parse(this.value);
            if (!info) {
                this.$el.html('');
                return;
            }
            
            _.each(info.content, function (k, v){
                k.index = v;
                k.amount = field_utils.format.float(k.amount, {digits: k.digits});
                if (k.date){
                    k.date = field_utils.format.date(field_utils.parse.date(k.date, {}, {isUTC: true}));
                }
            });
            this.$el.html(QWeb.render('ShowTaxInfo', {
                lines: info.content,
                outstanding: info.outstanding,
                title: info.title
            }));
        },       
    });
    
    field_registry.add('tax', ShowTaxLineWidget);
    
    });
    