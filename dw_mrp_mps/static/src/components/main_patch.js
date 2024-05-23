/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import MainComponent from '@mrp_mps/components/main';
import { loadJS, loadCSS } from '@web/core/assets'
const { onMounted, onWillStart } = owl
import { useBus } from "@web/core/utils/hooks";

patch(MainComponent.prototype, {
  setup() {
        super.setup();
        console.log("MainComponent this", this);
//        let dates = this.model.data.date_objs;
        let model = this.model;
        console.log("MainComponent model", model);

//        let dates = model.data.date_objs;
//        console.log("MainComponent dates", dates);
        onWillStart(async ()=>{
            await loadCSS("shared_assets/static/libs/css/daterangepicker.css")
        })
        onMounted(async ()=>{
            console.log("====== Inside Mounted Function =====")

            console.log('this.model',this.model)
            console.log('this.env.config',this.env.config)
            console.log('this.env.config.offset',this.env.config.offset)
            console.log('this.env.config.limit',this.env.config.limit)
             console.log("+++++productionScheduleIds+++++",this.model.data.production_schedule_ids)


//            this.model.data.dates.unshift('ssss 2025')
            console.log(this.model.data.manufacturing_period)
            let self = this
            $('input[name="dates"]').daterangepicker();
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
                    console.log("A new date selection was made: " + start.format('YYYY-MM-DD') + ' ------ to ----> ' + end.format('YYYY-MM-DD'));
                    self.model.load([], self.env.config.offset, self.env.config.limit, start.format('YYYY-MM-DD'), end.format('YYYY-MM-DD'));
                console.log('this.model',self.model)
                console.log('this.env.config',self.env.config)
                console.log('this.env.config.offset',self.env.config.offset)
                console.log('this.env.config.limit',self.env.config.limit)
                console.log("+++++productionScheduleIds+++++",self.model.data.production_schedule_ids)
              });
            });

        })
  },
   get manufacturingPeriodDates() {
        console.log('manufacturingPeriodDates',this.manufacturingPeriodDates);
        return this.model.data.date_objs;
   },

   onWillStart() {
        console.log('onWillStart');
        this.manufacturingPeriodDates = this.manufacturingPeriodDates;
        console.log('onWillStart',this.manufacturingPeriodDates);
   }


//  productionSchedule() {
//    console.log("this", this);
//    let _data = super.productionSchedule;
//    console.log("productionSchedule", _data);
//  },
});
