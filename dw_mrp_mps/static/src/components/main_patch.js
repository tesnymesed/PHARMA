/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import MainComponent from '@mrp_mps/components/main';
import { loadJS, loadCSS } from '@web/core/assets'
const { onMounted, onWillStart } = owl
import { useBus } from "@web/core/utils/hooks";

patch(MainComponent.prototype, {
  setup() {
        super.setup();
//        let dates = this.model.data.date_objs;
        let model = this.model;

//        let dates = model.data.date_objs;
        onWillStart(async ()=>{
            await loadCSS("shared_assets/static/libs/css/daterangepicker.css")
        })
        onMounted(async ()=>{
            $('input[name="dates"]').daterangepicker();
            var self = this;
            $(function() {
              $('input[name="daterange"]').daterangepicker({
                opens: 'left',
                ranges: {
                   'Today': [moment(), moment()],
                   'Yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
                   'Last 7 Days': [moment().subtract(6, 'days'), moment()],
                   'Last 30 Days': [moment().subtract(29, 'days'), moment()],
                   'This Month': [moment().startOf('month'), moment().endOf('month')],
                   'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
                }
              }, function(start, end, label) {
                    self.model.load([], start.format('YYYY-MM-DD'), end.format('YYYY-MM-DD'));
              });
            });

        })
  },
   get manufacturingPeriodDates() {
        return this.model.data.date_objs;
   },

   onWillStart() {
        this.manufacturingPeriodDates = this.manufacturingPeriodDates;
   }


//  productionSchedule() {
//    console.log("this", this);
//    let _data = super.productionSchedule;
//    console.log("productionSchedule", _data);
//  },
});
