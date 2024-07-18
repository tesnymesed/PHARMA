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
      await loadCSS("shared_assets/static/libs/css/tabulator.min.css");
    });

    onMounted(async () => {
      $('input[name="daterange"]').daterangepicker();
      var self = this;
      let conf = {
        opens: "right",
        ranges: {
          Today: [moment(), moment()],
          Yesterday: [
            moment().subtract(1, "days"),
            moment().subtract(1, "days"),
          ],
          "Last 7 Days": [moment().subtract(6, "days"), moment()],
          "Last 30 Days": [moment().subtract(29, "days"), moment()],
          "This Month": [moment().startOf("month"), moment().endOf("month")],
          "Last Month": [
            moment().subtract(1, "month").startOf("month"),
            moment().subtract(1, "month").endOf("month"),
          ],
        },
      };

      let params = this.props.action?.params;
      if (params) {
        let domain = params?.domain || this.props.action?.domain;
        console.log(
          "🚀 ~ onMounted ~ this.props.action?.domain:",
          this.props.action?.domain
        );
        let startDate = params?.startDate;
        let endDate = params?.endDate;

        if (startDate && endDate) {
          let _fStartDate = this.reformatDateString(startDate);
          let _fEndDate = this.reformatDateString(endDate);

          conf.startDate = _fStartDate;
          conf.endDate = _fEndDate;

          $("#daterange").data().daterangepicker.startDate = _fStartDate;
          $("#daterange").data().daterangepicker.endDate = _fEndDate;

          self.model.load(
            domain,
            self.env.config.offset,
            self.env.config.limit,
            startDate,
            endDate
          );
        }
      }

      $(function () {
        $('input[name="daterange"]').daterangepicker(
          conf,
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

      $("#daterange").data().daterangepicker.startDate = conf.startDate;
      $("#daterange").data().daterangepicker.endDate = conf.endDate;
    });
  },

  get manufacturingPeriodDates() {
    return this.model.data.date_objs;
  },

  get lowStockLines() {
    let res = [];
    let count = this.lines.map((item) =>
      item.forecast_ids.filter((f) => f.safety_stock_qty_wout_ss <= 0)
    );
    this.lines.forEach((item) => {
      const filteredForecastIds = item.forecast_ids.filter(
        (forecast) => forecast.safety_stock_qty_wout_ss <= 0
      );
      if (filteredForecastIds.length) {
        filteredForecastIds.forEach((alert) => {
          let prx = {
            id: item.id,
            product: item.product_id,
            product_id: item.product_id[0],
            product_name: item.product_id[1],
            ...alert,
          };
          res.push(prx);
        });
      }
    });
    return res;
  },

  onWillStart() {
    this.manufacturingPeriodDates = this.manufacturingPeriodDates;
  },

  reformatDateString(dateString) {
    // Split the dateString into year, month, and day components
    const [year, month, day] = dateString.split("-");

    // Construct the formatted date string
    return `${month}/${day}/${year}`;
  },

  displayAlerts() {
    $("#alertsModal").modal("show");
    this.initAlertsTable();
  },

  initAlertsTable() {
    let data = [];
    if (this.lines.length > 0) {
      data = this.lowStockLines;
      let keys = [
        "product_name",
        "date_start",
        //        "year",
        //        "quarter",
        "safety_stock_qty_wout_ss",
        // "required_capacity",
        // "production_objective_qty",
        "notes",
      ];

      var columns = [
        {
          title: "Period",
          field: "date_start",
        },

        {
          title: "Closing Stock Level",
          field: "safety_stock_qty_wout_ss",
        },
        {
          title: "Notes",
          field: "notes",
          editor: "textarea",
          formatter: "textarea",
          cellEdited: this.notesCellEdited.bind(this),
        },
      ];
      let alertsTable = this.initTabulator("#alertsTable", data, columns);
      //      alertsTable.on("tableBuilt", function () {
      //        alertsTable.redraw();
      //      });
    }
  },

  initTabulator(elt, data, columns) {
    var table = new Tabulator(elt, {
      height: "auto",
      layout: "fitColumns",
      columns: columns,
      data: data,
      groupBy: ["product_name"],
      groupHeader: function (value, count, data, group) {
        //value - the value all members of this group share
        //count - the number of rows in this group
        //data - an array of all the row data objects in this group
        //group - the group component for the group

        return (
          value +
          "<span style='color:#d00; margin-left:10px;'>(" +
          count +
          " item)</span>"
        );
      },
      pagination: true,
      paginationSize: 15,
      paginationSizeSelector: [15, 30, 45, 60, true],
      paginationCounter: "rows",
      paginationAddRow: "table",
    });
    return table;
  },

  async notesCellEdited(cell) {
    const notes = cell.getValue();
    const cellData = cell.getData();

    await this.model
      ._saveNotes(cellData.id, cellData.date_start, cellData.date_stop, notes)
      .then((result) => {})
      .catch((err) => {});
  },

  toggleModal() {
    // this.state.isModalVisible = !this.state?.isModalVisible;
    this.displayAlerts();
  },

  _onMouseOverStockAlert(ev) {
    const highCapacityCells = document.querySelectorAll(".low-stock");
    highCapacityCells.forEach((cell) => {
      cell.classList.add("flash-pop");
    });
    // this.model.mouseOverAlert();
  },

  _onMouseOutStockAlert(ev) {
    const highCapacityCells = document.querySelectorAll(".low-stock");
    highCapacityCells.forEach((cell) => {
      cell.classList.remove("flash-pop");
    });
    // this.model.mouseOutAlert();
  },

  //  productionSchedule() {
  //    console.log("this", this);
  //    let _data = super.productionSchedule;
  //    console.log("productionSchedule", _data);
  //  },
});
