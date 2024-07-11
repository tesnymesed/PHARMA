/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import MainComponent from "@mrp_mps/components/main";
import { loadJS, loadCSS } from "@web/core/assets";
const { onMounted, onWillStart } = owl;
import { useBus } from "@web/core/utils/hooks";

patch(MainComponent.prototype, {
  setup() {
    super.setup();
    //        let dates = this.model.data.date_objs;
    let model = this.model;

    //        let dates = model.data.date_objs;
    //        console.log("MainComponent dates", dates);

    onWillStart(async () => {
      await loadCSS("shared_assets/static/libs/css/daterangepicker.css");
    });

    onMounted(async () => {
      $('input[name="dates"]').daterangepicker();
      var self = this;
      $(function () {
        $('input[name="daterange"]').daterangepicker(
          {
            opens: "left",
            ranges: {
              Today: [moment(), moment()],
              Yesterday: [
                moment().subtract(1, "days"),
                moment().subtract(1, "days"),
              ],
              "Last 7 Days": [moment().subtract(6, "days"), moment()],
              "Last 30 Days": [moment().subtract(29, "days"), moment()],
              "This Month": [
                moment().startOf("month"),
                moment().endOf("month"),
              ],
              "Last Month": [
                moment().subtract(1, "month").startOf("month"),
                moment().subtract(1, "month").endOf("month"),
              ],
            },
          },
          function (start, end, label) {
            self.model.load(
              [],
              self.env.config.offset,
              self.env.config.limit,
              start.format("YYYY-MM-DD"),
              end.format("YYYY-MM-DD")
            );
          }
        );
      });

      let params = this.props.action?.params;
      console.log("🚀 ~ HOT PATCHED setup ~ params:", params);
      if (params) {
        let domain = params?.domain || this.props.action?.domain;
        console.log(
          "🚀 ~ onMounted ~ this.props.action?.domain:",
          this.props.action?.domain
        );
        let startDate = params?.startDate;
        let endDate = params?.endDate;
        if (startDate && endDate) {
          let picker = document.getElementById("daterange");

          // Construct the formatted date string
          let _fStartDate = this.reformatDateString(startDate);
          let _fEndDate = this.reformatDateString(endDate);
          console.log(
            "🚀 ~ onMounted ~ _fStartDate, _fEndDate:",
            _fStartDate,
            _fEndDate
          );

          picker.setAttribute("value", `${_fStartDate} - ${_fEndDate}`);

          console.log("🚀 ~ onMounted ~ picker.value:", picker.value);
          console.log("🚀 ~ onMounted ~ picker:", picker);

          //change the selected date range of that picker
          // picker.setStartDate(startDate);
          // picker.setEndDate(endDate);
          self.model.load(
            domain,
            self.env.config.offset,
            self.env.config.limit,
            startDate,
            endDate
          );
        }
      }
    });
  },

  get manufacturingPeriodDates() {
    return this.model.data.date_objs;
  },

  onWillStart() {
    console.log(
      "🚀 ~ onWillStart ~ this.props.action.params:",
      this.props.action.params
    );
    this.manufacturingPeriodDates = this.manufacturingPeriodDates;
  },

  reformatDateString(dateString) {
    // Split the dateString into year, month, and day components
    const [year, month, day] = dateString.split("-");

    // Construct the formatted date string
    return `${month}/${day}/${year}`;
  },

  //  productionSchedule() {
  //    console.log("this", this);
  //    let _data = super.productionSchedule;
  //    console.log("productionSchedule", _data);
  //  },
});
