odoo.define('kg_pos.selection_search', function(require) {
    'use_strict'

    var models = require('point_of_sale.models')
    var screens = require('point_of_sale.screens')
    var gui = require('point_of_sale.gui')
    var popups = require('point_of_sale.popups')
    var core = require('web.core')
    var field_utils = require('web.field_utils')
    var utils = require('web.utils');

    var _t = core._t
    var round_pr = utils.round_precision;
    var QWeb = core.qweb;

    var SelectionSearchPopupWidget = popups.extend({
        template: 'SelectionSearchPopupWidget',
        show: function(options){
            var self = this;
            options = options || {};
            this._super(options);
    
            this.list = options.list || [];
            this.is_selected = options.is_selected || function (item) { return false; };
            this.renderElement();
            this.enable_keypress = true
            var search_timeout  = null;
            
            this.$('#input-search').on('input',function(event){
                var input, filter;
                input = document.getElementById('input-search')
                filter = input.value.toUpperCase();
                for (i = 0; i < list.length; i++) {
                    a = $(`[data-item-index='${i}']`)[0];
                    txtValue = a.textContent || a.innerText;
                    if (txtValue.toUpperCase().indexOf(filter) > -1) {
                        list[i].style.display = "";
                    } 
                    else {
                        list[i].style.display = "none";
                    }
                }
            });

            this.$('.searchbox .search-clear').click(function(){
                self.clear_search();
            });
        },
        click_item : function(event) {
            this.gui.close_popup();
            if (this.options.confirm) {
                var item = this.list[parseInt($(event.target).data('item-index'))];
                item = item ? item.item : item;
                this.options.confirm.call(self,item);
            }
        },
    });
    gui.define_popup({name:'selection-search', widget: SelectionSearchPopupWidget});
})
