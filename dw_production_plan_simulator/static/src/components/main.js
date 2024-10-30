/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
// import {
//   MrpMpsControlPanel,
//   MrpMpsSearchBar,
// } from "../search/mrp_mps_control_panel";
// import { MrpMpsSearchModel } from "../search/mrp_mps_search_model";
import ProductionPlanSimulatorLine from "@dw_production_plan_simulator/components/line";
import { ProductionPlanSimulatorModel } from "@dw_production_plan_simulator/models/production_plan_simulator_model";
import { registry } from "@web/core/registry";
import { useService, useBus } from "@web/core/utils/hooks";
import { CheckBox } from "@web/core/checkbox/checkbox";
import { usePager } from "@web/search/pager_hook";
import { useSetupAction } from "@web/webclient/actions/action_hook";
import { WithSearch } from "@web/search/with_search/with_search";
import { ActionMenus } from "@web/search/action_menus/action_menus";
import { download } from "@web/core/network/download";
import { ExportDataDialog } from "@web/views/view_dialogs/export_data_dialog";
import MainComponent from "@mrp_mps/components/main";

import {
  Component,
  onWillStart,
  useSubEnv,
  useRef,
  onPatched,
  onMounted,
  useState,
} from "@odoo/owl";
import { loadJS, loadCSS } from "@web/core/assets";
class ProductionPlanSimulatorComponent extends Component {
  //--------------------------------------------------------------------------
  // Lifecycle
  //--------------------------------------------------------------------------
  setup() {
    this.action = useService("action");
    this.dialog = useService("dialog");
    this.orm = useService("orm");
    this.viewService = useService("view");
    this.rpc = useService("rpc");
    this.notificationService = useService("notification");
    this.state = useState({
      domain: [],
      companies: [],
      products: [],
      simulationLines: [],
      workCenterCapacities: [],
      decisionActions: [],
      currentCompanyId: null,
      currentCompanyName: "",
      startDate: "2024-01-01",
      endDate: "2025-06-01",
      salesStartDate: "2024-01-01",
      salesEndDate: "2024-03-01",
      isModalVisible: false,
      planningCycle: "",
      planningDate: null,
    });
    this.data = {};

    const { orm, action, dialog } = this;
    this.model = new ProductionPlanSimulatorModel(this.props, {
      orm,
      action,
      dialog,
    });
    this.withSearchProps = null;

    useSubEnv({
      manufacturingPeriods: [],
      model: this.model,
      defaultPageLimit: 20,
      config: {
        ...this.env.config,
        offset: 0,
        limit: 20,
        mpsImportRecords: true,
      },
    });

    useSetupAction({
      getContext: () => {
        return this.props.action.context;
      },
    });

    useBus(this.model, "update", () => this.render(true));

    onWillStart(async () => {
      //      await loadCSS(
      //        "dw_production_plan_simulator/static/src/libs/css/core.css"
      //      );
      //      await loadCSS(
      //        "dw_production_plan_simulator/static/src/libs/css/theme-default.css"
      //      );
      await loadCSS(
        "dw_production_plan_simulator/static/src/libs/css/perfect-scrollbar.css"
      );
      await loadCSS("shared_assets/static/libs/css/daterangepicker.css");
      await loadCSS("shared_assets/static/libs/css/tabulator.6.2.min.css");
      //      await loadCSS("shared_assets/static/libs/css/tabulator.min.css");
      await loadCSS(
        "dw_production_plan_simulator/static/src/components/main.css"
      );

      await loadJS(
        "dw_production_plan_simulator/static/src/libs/js/perfect-scrollbar.js"
      );
      await loadJS(
        "dw_production_plan_simulator/static/src/libs/js/helpers.js"
      );
      await loadJS("dw_production_plan_simulator/static/src/libs/js/menu.js");
      await loadJS("dw_production_plan_simulator/static/src/libs/js/main.js");
      await loadJS(
        "dw_production_plan_simulator/static/src/libs/js/buttons.js"
      );

      await loadJS("shared_assets/static/libs/js/jsuites.js");
      await loadCSS("shared_assets/static/libs/css/jsuites.css");

      this.env.config.setDisplayName(_t("Production Plan Simulation Tool"));

      this.state.currentCompanyId = parseInt($("#select-company").val());
      this.state.currentCompanyName = $(
        "#select-company option:selected"
      ).text();

      this.state.domain = [["company_id", "=", this.state.currentCompanyId]];

      await this.model.load(
        this.state.domain,
        this.env.config.offset,
        this.env.config.limit,
        this.state.startDate,
        this.state.endDate
      );

      //      this._MPSAction = await this.orm.call(
      //        "dw.production.plan.simulation",
      //        "dw_action_open_mps_view",
      //        [this.state.currentCompanyId, this.state]
      //      );
      //      console.log(
      //        "🚀 ~ ProductionPlanSimulatorComponent ~ setup ~ this._MPSAction:",
      //        this._MPSAction
      //      );
    });

    onMounted(async () => {
      var self = this;
      this.initFilterSettings();
      //      this.initAlertsTable();
      this.captureInputSettings();

      await self.model
        .load(
          this.state.domain,
          self.env.config.offset,
          self.env.config.limit,
          self.state.startDate,
          self.state.endDate
        )
        .then((result) => {
          self.data = result;
        })
        .catch((error) => {
          console.error(error);
        });

      $("#submit").click(
        async function () {
          this.captureInputSettings();

          await self.model.load(
            this.state.domain,
            self.env.config.offset,
            self.env.config.limit,
            self.state.startDate,
            self.state.endDate
          );
        }.bind(this)
      );

      $('input[id="plan-date-range"]').on(
        "apply.daterangepicker",
        function (ev, picker) {}
      );

      $('input[id="sales-avg-period"]').on(
        "apply.daterangepicker",
        function (ev, picker) {}
      );
    });

    usePager(() => {
      return {
        offset: this.env.config.offset,
        limit: this.env.config.limit,
        total: this.model?.data.count,
        onUpdate: async ({ offset, limit }) => {
          this.env.config.offset = offset;
          this.env.config.limit = limit;
          this.model.load(undefined, offset, limit);
        },
      };
    });
  }

  initCompaniesSelect(id) {
    var companiesData = this.getCompanies();
    companiesData
      .then((result) => {
        this.state.companies = companiesData;
        var companiesSelect = document.getElementById(id);
        companiesSelect.innerHTML = "";
        result.forEach(
          function (opt, i) {
            var option = this.addSelectOption(opt["name"], opt["id"]);
            option.selected = i === 0 ? true : false;
            companiesSelect.appendChild(option);
          }.bind(this)
        );
      })
      .catch((error) => {
        console.error(error); // Handle any errors
      });
  }

  initPeriodInput() {
    var self = this;
    $('input[name="daterange"]').daterangepicker(
      {
        opens: "left",
        ranges: {
          Today: [moment(), moment()],
          "This Year": [moment().startOf("year"), moment().endOf("year")],
          "18 Months": [
            moment().startOf("year"),
            moment().add(17, "months").endOf("year"),
          ],
          "Next 18 Months": [
            moment().add(1, "day"),
            moment().add(18, "months").endOf("month"),
          ],
          "24 Months": [
            moment().startOf("year"),
            moment().add(23, "months").endOf("year"),
          ],
          "Next 24 Months": [
            moment().startOf("month"),
            moment().add(24, "months").endOf("month"),
          ],
          "Last Year": [
            moment().subtract(1, "year").startOf("year"),
            moment().subtract(1, "year").endOf("year"),
          ],
          "Last Month": [
            moment().subtract(1, "month").startOf("month"),
            moment().subtract(1, "month").endOf("month"),
          ],
          "This Month": [moment().startOf("month"), moment().endOf("month")],
        },
      },
      function (start, end, label) {
        let startDate = start.format("YYYY-MM-DD");
        let endDate = end.format("YYYY-MM-DD");
      }
    );
  }

  initPlanningCycleSelect(id) {
    var planningCycleOptions = [
      {
        id: "monthly",
        name: "Monthly",
      },
      {
        id: "annual",
        name: "Annual",
      },
    ];

    var planCycleSelect = document.getElementById(id);
    planCycleSelect.innerHTML = "";
    planningCycleOptions.forEach(
      function (opt, i) {
        var option = this.addSelectOption(opt["name"], opt["id"]);
        option.selected = i === 0 ? true : false;
        planCycleSelect.appendChild(option);
      }.bind(this)
    );
  }

  initCalendarInput(id, key, _type, date = new Date()) {
    var dateValue;
    if (typeof date === "string" || date instanceof Date) {
      dateValue = new Date(date); // This will work for both string and Date object
    } else {
      dateValue = new Date(); // Default to the current date
    }
    var self = this;
    jSuites.calendar(document.getElementById(id), {
      type: "year-month-picker",
      format: "MMM-YYYY",
      value: dateValue,
      // validRange: ["2024-02-01", "2025-12-31"],
      onchange: function (instance, value) {
        try {
          self.state[key] = self.formatStringDate(value, _type);
        } catch (error) {
          console.error(
            "��� ~ ProductionPlanSimulatorComponent ~ jSuites.calendar ~ error:",
            error
          );
        }
      },
    });
  }

  formatStringDate(dateString, _type) {
    const date = new Date(dateString);

    // Check if the date is valid
    if (isNaN(date.getTime())) {
      throw new Error("Invalid date format");
    }

    // Get the year, month, and day in local time
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0"); // Months are 0-indexed
    const day = String(date.getDate()).padStart(2, "0");

    const formattedDate = `${year}-${month}-${day}`;

    if (_type === "start") {
      return formattedDate; // Return the formatted date for "start"
    } else if (_type === "end") {
      // Get the last day of the month in local time
      const endOfMonth = new Date(date.getFullYear(), date.getMonth() + 1, 0);
      const endYear = endOfMonth.getFullYear();
      const endMonth = String(endOfMonth.getMonth() + 1).padStart(2, "0");
      const endDay = String(endOfMonth.getDate()).padStart(2, "0");
      return `${endYear}-${endMonth}-${endDay}`; // Return the last day of the month
    } else {
      throw new Error("Type must be 'start' or 'end'");
    }
  }

  initFilterSettings() {
    this.initCompaniesSelect("select-company");
    //    this.initPlanningCycleSelect("select-planning-cycle");

    //    this.initCalendarInput("planning-period", "planningDate", "start");

    this.initCalendarInput(
      "plan-date-range-start",
      "startDate",
      "start",
      new Date(new Date().getFullYear(), 0, 1)
    );
    this.initCalendarInput(
      "plan-date-range-end",
      "endDate",
      "end",
      new Date(new Date().getFullYear(), 11, 31)
    );

    this.initCalendarInput("sales-avg-range-start", "salesStartDate", "start");
    this.initCalendarInput("sales-avg-range-end", "salesEndDate", "end");

    // this.initPeriodInput();
  }

  async getCompanies() {
    var companies = this.orm.searchRead(
      "res.company",
      [[1, "=", 1]],
      ["id", "name"],
      { order: "id ASC" }
    );
    var res = [];
    await companies
      .then((result) => {
        res = result;
        this.state.companies = result;
      })
      .catch((error) => {
        console.error(error);
      });
    return res;
  }

  addSelectOption(text, value) {
    var option = document.createElement("option");
    option.text = text;
    option.value = value; // Set both text and value to the same value
    return option;
  }

  initTabulator(elt, data, columns) {
    var table = new Tabulator(elt, {
      height: "auto",
      layout: "fitColumns",
      columns: columns,
      data: data,
      groupBy: ["workcenter_name", "year", "quarter"],
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
      history: true,
      pagination: "local",
      paginationSize: 12,
      // paginationSizeSelector: [12, 18, 24, 30],
      paginationCounter: "rows",
      movableColumns: true,
      columnDefaults: {
        tooltip: true,
      },
    });
    return table;
  }

  initAlertsTable() {
    let data = this.workCenterCapacities;
    if (this.workCenterCapacities.length > 0) {
      // data = this.workCenterCapacities.filter(
      //   (cp) => cp.capacity_utilisation >= 90
      // );
      let keys = [
        //        "workcenter",
        "date_start",
        //        "year",
        //        "quarter",
        "capacity_utilisation",
        "required_capacity",
        "production_objective_qty",
        "decision",
        "alert_notes",
      ];

      // let columns = this.prepareTableColumns(keys);

      // let columns = [
      //   {
      //     title: "Date Start",
      //     field: "date_start",
      //   },
      //   {
      //     title: "Capacity Utilisation",
      //     field: "capacity_utilisation",
      //   },
      //   {
      //     title: "Required Capacity",
      //     field: "required_capacity",
      //   },
      //   {
      //     title: "Production Objective Qty",
      //     field: "production_objective_qty",
      //   },
      //   {
      //     title: "Notes",
      //     field: "alert_notes",
      //     editor: "textarea",
      //     formatter: "textarea",
      //   },
      // ];

      var columns = [
        {
          title: "Date Start",
          field: "date_start",
        },

        {
          title: "Required Capacity",
          field: "required_capacity",
        },
        {
          title: "Production Objective Qty",
          field: "production_objective_qty",
        },

        {
          title: "Capacity Utilisation",
          field: "capacity_utilisation",
          formatter: function (cell, formatterParams, onRendered) {
            var value = cell.getValue();
            var color;

            if (value < 50) {
              color = "green";
            } else if (value >= 50 && value <= 100) {
              color = "orange";
            } else {
              color = "red";
            }

            // return color;
            return `<span style="color: ${color};">${value} %</span>`;
          },
          formatterParams: {
            precision: 2,
            symbol: " %",
            // symbolAfter: "p",
            min: 0,
            color: function (cell, formatterParams, onRendered) {
              var value = cell.getValue();
              var color;

              if (value < 50) {
                color = "green";
              } else if (value >= 50 && value <= 100) {
                color = "orange";
              } else {
                color = "red";
              }

              return color;
              return `<span style="color: ${color};">${value}%</span>`;
            },
            legend: false,
          },
        },
        {
          title: "Decision",
          field: "decision",
          editable: true,
          formatter: "lookup",
          formatterParams: this.decisionActions,
          editor: "list",
          editorParams: { values: this.decisionActions },
          cellEdited: this.alertDecisionCellEdited.bind(this),
        },
        {
          title: "Notes",
          field: "alert_notes",
          editor: "textarea",
          formatter: "textarea",
          cellEdited: this.alertNotesCellEdited.bind(this),
        },
      ];
      let alertsTable = this.initTabulator("#alertsTable", data, columns);
      //      alertsTable.on("tableBuilt", function () {
      //        alertsTable.redraw();
      //      });
    }
  }

  prepareTableColumns(columns) {
    if (columns.length > 0) {
      var columnsUp = columns.map((key) => {
        return {
          title: key,
          field: key,
        };
      });
      return columnsUp;
    } else {
      return [];
    }
  }

  get companies() {
    return this.state?.companies;
  }

  get manufacturingPeriods() {
    return this.model?.data?.dates || [];
  }

  get simulationLines() {
    this.state.simulationLines = this.model?.data?.production_simulation_ids;
    return this.model?.data?.production_simulation_ids;
  }

  get workCenters() {
    return d3
      .nest()
      .key((d) => d.workcenter_id)
      .entries(this.simulationLines);
  }

  get workCenterCapacities() {
    this.state.workCenterCapacities = this.model?.data?.workcenter_capacities;
    return this.model?.data?.workcenter_capacities;
  }

  get decisionActions() {
    this.state.decisionActions = this.model?.data?.decision_action_ids;
    return this.model?.data?.decision_action_ids;
  }

  //
  get groups() {
    return this.model?.data.groups[0];
  }
  //
  get isSelected() {
    return this.model.selectedRecords.size === this.simulationLines.length;
  }
  //
  toggleSelection() {
    this.model.toggleSelection();
  }

  captureInputSettings() {
    this.state.currentCompanyId = parseInt(
      $("#select-company option:selected").val()
    );
    this.state.currentCompanyName = $("#select-company option:selected").text();

    // TODO: Alter to calendar
    // let picker = $('input[id="plan-date-range"]').data("daterangepicker");
    // this.state.startDate = picker.startDate.format("YYYY-MM-DD");
    // this.state.endDate = picker.endDate.format("YYYY-MM-DD");

    // let salesPicker = $('input[id="sales-avg-period"]').data("daterangepicker");
    // this.state.salesStartDate = salesPicker.startDate.format("YYYY-MM-DD");
    // this.state.salesEndDate = salesPicker.endDate.format("YYYY-MM-DD");

    //    this.state.planningCycle = $(
    //      "#select-planning-cycle option:selected"
    //    ).val();

    //    this.getCalendarValue("planning-period", "planningDate", "start");

    this.getCalendarValue("plan-date-range-start", "startDate", "start");
    this.getCalendarValue("plan-date-range-end", "endDate", "end");

    this.getCalendarValue("sales-avg-range-start", "salesStartDate", "start");
    this.getCalendarValue("sales-avg-range-end", "salesEndDate", "end");

    this.state.domain = [["company_id", "=", this.state.currentCompanyId]];

    this.model.saveDateRange(
      this.state.currentCompanyId,
      this.state.startDate,
      this.state.endDate
    );

    this.model.saveSalesDateRange(
      this.state.currentCompanyId,
      this.state.salesStartDate,
      this.state.salesEndDate
    );
  }

  getCalendarValue(id, key, _type) {
    let calendarElVal = document.getElementById(id).calendar.getValue();
    if (calendarElVal) {
      try {
        this.state[key] = this.formatStringDate(calendarElVal, _type);
      } catch (error) {
        console.error(
          "��� ~ ProductionPlanSimulatorComponent ~ getCalendarValue ~ error:",
          error
        );
      }
    }
  }

  /**
   * Handles the daterange input change.
   * @private
   * @param {Event} ev
   */
  _onChangeDateRange(ev) {}

  async _onChangeCompany(ev, productionSimulationId) {
    this.state.currentCompanyId = parseInt(ev.target.value);
    this.captureInputSettings();
  }

  async _onChangePlanningCycle(ev) {
    this.state.planningCycle = ev.target.value;
    this.captureInputSettings();
  }

  //
  //    /**
  //     * Handles the click on replenish button. It will call action_replenish with
  //     * all the Ids present in the view.
  //     *
  //     * @private
  //     * @param {MouseEvent} ev
  //     */
  //    _onClickReplenish(ev) {
  //        this.model.replenishAll();
  //    }
  //

  // t-on-mouseover.stop="_onMouseOverProdPlanAlert"
  // t-on-mouseout.stop="_onMouseOutProdPlanAlert"
  _onMouseOverCapacityAlert(ev) {
    const highCapacityCells = document.querySelectorAll(".high-capacity");
    highCapacityCells.forEach((cell) => {
      cell.classList.add("flash-pop");
    });

    // this.model.mouseOverAlert();
  }

  _onMouseOutCapacityAlert(ev) {
    const highCapacityCells = document.querySelectorAll(".high-capacity");
    highCapacityCells.forEach((cell) => {
      cell.classList.remove("flash-pop");
    });
    // this.model.mouseOutAlert();
  }
  //
  async _onClickCreate(ev) {
    this.captureInputSettings();
    this.model._createProducts(this.state.currentCompanyId);

    await this.model.load(
      this.state.domain,
      this.env.config.offset,
      this.env.config.limit,
      this.state.startDate,
      this.state.endDate
    );

    if (this.model.data.length > 0) {
      var createProductNotif = this.notificationService.add(
        _t(
          "Load Products to " +
            companyName +
            "'s site Production Simulation successful"
        ),
        {
          title: _t(
            "Load Products to " +
              this.state.currentCompanyName +
              "'s site Production Simulation successful"
          ),
          type: "success",
        }
      );
      setTimeout(createProductNotif, 3000);
      setTimeout(function () {
        location.reload(true);
      }, 3000);
    } else {
      var createProductNotif = this.notificationService.add(
        _t(
          "No products were found in " +
            this.state.currentCompanyName +
            "'s site "
        ),
        {
          title: _t(
            "Load Products to " +
              this.state.currentCompanyName +
              "'s site Production Simulation failed"
          ),
          type: "danger",
        }
      );
      setTimeout(createProductNotif, 3000);
    }
  }

  displayAlerts() {
    $("#alerts-modal").modal("show");
    this.initAlertsTable();
  }

  toggleModal() {
    this.state.isModalVisible = !this.state.isModalVisible;
    this.displayAlerts();
  }

  closeAlertsModal() {
    $("#alerts-modal").modal("hide");
  }

  async alertNotesCellEdited(cell) {
    const notes = cell.getValue();
    const cellData = cell.getData();

    await this.model
      ._saveAlertNotes(
        cellData.id,
        cellData.date_start,
        cellData.date_stop,
        notes
      )
      .then((result) => {})
      .catch((err) => {});
  }

  async alertDecisionCellEdited(cell) {
    const decision = cell.getValue();
    const cellData = cell.getData();
    await this.model
      ._saveDecision(
        cellData.id,
        cellData.date_start,
        cellData.date_stop,
        decision
      )
      .then((result) => {})
      .catch((err) => {});
  }

  _createMasterProductionSchedule() {
    this.model
      ._createMPSEntries(this.state.currentCompanyId, this.simulationLines)
      .then((res) => {
        var createMPSentriesNotif = this.notificationService.add(
          _t("You will be redirected shortly..."),
          {
            title: _t(
              this.state.currentCompanyName +
                "'s site Master production schedule (MRP) update successful"
            ),
            type: "success",
          }
        );
        setTimeout(createMPSentriesNotif, 3000);
        // setTimeout(function () {
        //   location.reload(true);
        // }, 3000);
        this.model._openMPS(res, this.state);
        // this.load([["company_id", "=", state.currentCompanyId]]);
        // return this.data;
        //                if (productionSimulationIds.length === 1) {
        //                    this.reload(productionSimulationIds[0]);
        //                } else {
        //                    this.load();
        //                }
      })
      .catch((error) => {
        console.error("error", error);
        var createMPSentriesNotif = this.notificationService.add(
          _t(
            this.state.currentCompanyName +
              "'s site Master production schedule (MRP) creation error: \n" +
              error
          ),
          {
            title: _t("Error"),
            type: "danger",
          }
        );
        setTimeout(createMPSentriesNotif, 3000);
        return error;
      });
  }

  _onClickWorkCenterLink(ev, id) {
    const ID = parseInt(id.split(",")[0].trim(), 10);
    this.action.doAction({
      type: "ir.actions.act_window",
      res_model: ev.currentTarget.dataset.model,
      res_id: ID,
      views: [[false, "form"]],
      context: { dw_pharma_simulation: true },
      target: "new",
    });
  }

  _onClickWorkCenterEdit(ev, id) {
    this.model._editWorkCenter(id);
  }

  //
  //    get actionMenuItems() {
  //        return {
  //            action: [
  //                {
  //                    key: "export",
  //                    description: _t("Export"),
  //                    callback: () => this.onExportData(),
  //                },
  //                {
  //                    key: "delete",
  //                    description: _t("Delete"),
  //                    callback: () => this.unlinkSelectedRecord(),
  //                },
  //                {
  //                    key: "replenish",
  //                    description: _t("Replenish"),
  //                    callback: () => this.replenishSelectedRecords(),
  //                },
  //            ],
  //        };
  //    }
  //
  //
  //    async downloadExport(fields, import_compat, format) {
  //        const resIds = Array.from(this.model.selectedRecords);
  //        const exportedFields = fields.map((field) => ({
  //            name: field.name || field.id,
  //            label: field.label || field.string,
  //            store: field.store,
  //            type: field.field_type,
  //        }));
  //        if (import_compat) {
  //            exportedFields.unshift({ name: "id", label: _t("External ID") });
  //        }
  //        await download({
  //            data: {
  //                data: JSON.stringify({
  //                    import_compat,
  //                    context: this.props.context,
  //                    domain: this.model.domain,
  //                    fields: exportedFields,
  //                    ids: resIds.length > 0 && resIds,
  //                    model: "dw.production.plan.simulation",
  //                }),
  //            },
  //            url: `/web/export/${format}`,
  //        });
  //    }
  //
  //    /**
  //     * Opens the Export Dialog
  //     *
  //     * @private
  //     */
  //    onExportData() {
  //        const dialogProps = {
  //            context: this.props.context,
  //            defaultExportList: [],
  //            download: this.downloadExport.bind(this),
  //            getExportedFields: this.getExportedFields.bind(this),
  //            root: {
  //                resModel: "dw.production.plan.simulation",
  //                activeFields: [],
  //            },
  //        };
  //        this.dialog.add(ExportDataDialog, dialogProps);
  //    }
}

ProductionPlanSimulatorComponent.template =
  "production_plan_simulator.prod_plan_sim_template";
ProductionPlanSimulatorComponent.components = {
  //  MainComponent,
  // WithSearch,
  ProductionPlanSimulatorLine,
  CheckBox,
  // MrpMpsSearchBar,
  ActionMenus,
};

registry
  .category("actions")
  .add(
    "dw_production_plan_simulator.prod_plan_sim_client_action",
    ProductionPlanSimulatorComponent
  );

export default ProductionPlanSimulatorComponent;

registry.category("actions").add("dw_mrp_mps_client_action", MainComponent);
