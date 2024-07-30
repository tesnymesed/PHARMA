/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import MainComponent from "@mrp_mps/components/main";
import { loadJS, loadCSS } from "@web/core/assets";
const { onMounted, onWillStart } = owl;
import { useBus } from "@web/core/utils/hooks";

patch(MainComponent.prototype, {
  createSupplyPlans() {
    let picker = $("#daterange").data("daterangepicker");
    let startDate = picker.startDate.format("YYYY-MM-DD");
    let endDate = picker.endDate.format("YYYY-MM-DD");
    console.log("createSupplyPlan", this.lines);
    this.model._createSupplyPlans(startDate, endDate);
  },
});
