/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
//import { MrpMpsControlPanel, MrpMpsSearchBar } from "../search/mrp_mps_control_panel";
//import { MrpMpsSearchModel } from '../search/mrp_mps_search_model';
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
      currentCompanyId: null,
      startDate: "2024-01-01",
      endDate: "2025-06-01",
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

    //        useBus(this.model, "update", () => this.render(true));

    onWillStart(async () => {
      //      await loadCSS(
      //        "dw_production_plan_simulator/static/src/libs/css/core.css"
      //      );
      //      await loadCSS(
      //        "dw_production_plan_simulator/static/src/libs/css/theme-default.css"
      //      );
      //      await loadCSS(
      //        "dw_production_plan_simulator/static/src/libs/css/perfect-scrollbar.css"
      //      );
      await loadCSS("shared_assets/static/libs/css/daterangepicker.css");

      //      await loadJS(
      //        "dw_production_plan_simulator/static/src/libs/js/perfect-scrollbar.js"
      //      );
      await loadJS(
        "dw_production_plan_simulator/static/src/libs/js/helpers.js"
      );
      await loadJS("dw_production_plan_simulator/static/src/libs/js/menu.js");
      await loadJS("dw_production_plan_simulator/static/src/libs/js/main.js");
      await loadJS(
        "dw_production_plan_simulator/static/src/libs/js/buttons.js"
      );

      this.env.config.setDisplayName(_t("Production Plan Simulation Tool"));

      this.state.currentCompanyId = parseInt($("#select-company").val());

      this.state.domain = [["company_id", "=", this.state.currentCompanyId]];

      await this.model.load(
        this.state.domain,
        this.env.config.offset,
        this.env.config.limit,
        this.state.startDate,
        this.state.endDate
      );
      console.log("this.model.data", this.model.data);
      console.log("onWillStart simulationLines", this.simulationLines);
      console.log(
        "onWillStart manufacturingPeriods",
        this.manufacturingPeriods
      );
    });

    onMounted(async () => {
      var self = this;
      this.initFilterSettings();
      //      this.initSimulatorTable();
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
      console.log("onMounted self.model.data", self.model.data);
      console.log("onMounted simulationLines", self.simulationLines);

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
          console.log("self.model.data", self.model.data);
          console.log("simulationLines", self.simulationLines);
        }.bind(this)
      );

      $('input[id="select-period"]').on(
        "apply.daterangepicker",
        function (ev, picker) {
          console.log(
            "apply.daterangepicker",
            picker.startDate.format("YYYY-MM-DD")
          );
          console.log(
            "apply.daterangepicker",
            picker.endDate.format("YYYY-MM-DD")
          );
        }
      );
    });

    //        usePager(() => {
    //            return {
    //                offset: this.env.config.offset,
    //                limit: this.env.config.limit,
    //                total: this.model?.data.count,
    //                onUpdate: async ({ offset, limit }) => {
    //                    this.env.config.offset = offset;
    //                    this.env.config.limit = limit;
    //                    this.model.load(undefined, offset, limit);
    //                },
    //            };
    //        });
  }

  initCompaniesSelect() {
    var companiesData = this.getCompanies();
    companiesData
      .then((result) => {
        this.state.companies = companiesData;
        var companiesSelect = document.getElementById("select-company");
        companiesSelect.innerHTML = "";
        result.forEach(
          function (opt, i) {
            var option = this.addSelectOption(opt["name"], opt["id"]);
            option.selected = index === 0 ? true : false;
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

  initFilterSettings() {
    this.initCompaniesSelect();
    this.initPeriodInput();
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
      movableColumns: true,
      pagination: "local",
      paginationSize: 6,
      paginationSizeSelector: [3, 5, 8, 12, 20, 30],
      paginationCounter: "rows",
    });
    return table;
  }

  initSimulatorTable() {
    let simulatorTable = this.initTabulator(
      "#simulatorTable",
      ["id", "name"],
      this.state.companies
    );
    simulatorTable.on("tableBuilt", function () {
      simulatorTable.redraw();
    });
  }

  get companies() {
    return this.state?.companies;
  }

  get manufacturingPeriods() {
    return this.model?.data?.dates || [];
  }

  get simulationLines() {
    console.log(
      " get simulationLines()  this.model?.data?.production_simulation_ids",
      this.model?.data?.production_simulation_ids
    );
    this.state.simulationLines = this.model?.data?.production_simulation_ids;
    return this.model?.data?.production_simulation_ids;
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
    this.state.currentCompanyId = parseInt($("#select-company").val());

    let picker = $('input[id="select-period"]').data("daterangepicker");
    this.state.startDate = picker.startDate.format("YYYY-MM-DD");
    this.state.endDate = picker.endDate.format("YYYY-MM-DD");

    this.state.domain = [["company_id", "=", this.state.currentCompanyId]];

    console.log("captureInputSettings startDate", this.state.startDate);
    console.log("captureInputSettings endDate", this.state.endDate);
    console.log("captureInputSettings this.state.domain", this.state.domain);
    console.log(
      "captureInputSettings currentCompanyId",
      this.state.currentCompanyId
    );

    this.model.saveDateRange(
      this.state.currentCompanyId,
      this.state.startDate,
      this.state.endDate
    );
  }
  /**
   * Handles the daterange input change.
   * @private
   * @param {Event} ev
   */
  _onChangeDateRange(ev) {
    console.log("_onChangeDateRange", ev);
  }

  async _onChangeCompany(ev, productionSimulationId) {
    console.log(
      "_onChangeCompany(ev, productionSimulationId)",
      ev,
      productionSimulationId
    );
    this.state.currentCompanyId = parseInt(ev.target.value);
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
  //    _onMouseOverReplenish(ev) {
  //        this.model.mouseOverReplenish();
  //    }
  //
  //    _onMouseOutReplenish(ev) {
  //        this.model.mouseOutReplenish();
  //    }
  //
  async _onClickCreate(ev) {
    this.captureInputSettings();
    this.model._createProducts(this.state);

    await this.model.load(
      this.state.domain,
      this.env.config.offset,
      this.env.config.limit,
      this.state.startDate,
      this.state.endDate
    );
    console.log("this.simulationLines", this.simulationLines);
    console.log("this.state.simulationLines", this.state.simulationLines);

    if (this.model.data.length > 0) {
      var createProductNotif = this.notificationService.add(
        "Load Products to " +
          this.state.companies +
          " Production Simulation successful",
        {
          title:
            "Load Products to " +
            this.state.companies +
            " Production Simulation successful",
          type: "success",
        }
      );
      setTimeout(createProductNotif, 2000);
      setTimeout(function () {
        location.reload(true);
      }, 2000);
    } else {
      var createProductNotif = this.notificationService.add(
        "No products were found. ",
        {
          title:
            "Load Products to " +
            this.state.companies +
            " Production Simulation successful",
          type: "danger",
        }
      );
      setTimeout(createProductNotif, 2000);
    }
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
  //    MrpMpsControlPanel,
  //    WithSearch,
  ProductionPlanSimulatorLine,
  CheckBox,
  //    MrpMpsSearchBar,
  //    ActionMenus,
};

registry
  .category("actions")
  .add(
    "dw_production_plan_simulator.prod_plan_sim_client_action",
    ProductionPlanSimulatorComponent
  );

export default ProductionPlanSimulatorComponent;
