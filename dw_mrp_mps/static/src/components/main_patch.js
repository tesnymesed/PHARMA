/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import MainComponent from '@mrp_mps/components/main';

patch(MainComponent.prototype, {
  setup() {
        super.setup();
        console.log("MainComponent this", this);
//        let dates = this.model.data.date_objs;
        let model = this.model;
        console.log("MainComponent model", model);
//        let dates = model.data.date_objs;
//        console.log("MainComponent dates", dates);
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
