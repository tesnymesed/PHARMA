/** @odoo-module **/

import { CheckBox } from "@web/core/checkbox/checkbox";
import { useService, useBus } from "@web/core/utils/hooks";
import { formatFloat } from "@web/core/utils/numbers";
import { Component, useRef, onPatched } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

export default class ProductionPlanSimulatorLine extends Component {
  setup() {
    this.actionService = useService("action");
    this.dialogService = useService("dialog");
    this.orm = useService("orm");
    this.notificationService = useService("notification");
    this.model = this.env.model;
    this.forecastRow = useRef("forecastRow");
    this.replenishRow = useRef("replenishRow");

    this.salesObjRow = useRef("salesObjRow");
    this.prodObjRow = useRef("prodObjRow");
    this.salesHistoryRow = useRef("salesHistoryRow");
    this.prodPlanRow = useRef("prodPlanRow");
    this.prodPlanBatchesRow = useRef("prodPlanBatchesRow");
    this.suggProdPlanRow = useRef("suggProdPlanRow");
    this.suggProdPlanBatchesRow = useRef("suggProdPlanBatchesRow");

    this.formVals = {
      title: "",
      headerTitle: "",
      modalPeriodText: "",
      notes: "",
      batch_count: 0.0,
      eff_planned_production_batches: 0.0,
    };
    // this.formVals = {};

    onPatched(() => {
      // after a replenishment, switch to next column if possible
      const previousEl =
        this.replenishRow.el.getElementsByClassName("o_prod_sim_hover")[0];
      if (previousEl) {
        previousEl.classList.remove("o_prod_sim_hover");
        const el = this.replenishRow.el.getElementsByClassName(
          "o_prod_sim_forced_replenish"
        )[0];
        if (el) {
          el.classList.add("o_prod_sim_hover");
        }
      }
    });

    useBus(this.model, "mouse-over", () => this._onMouseOverProdPlanAlert());
    useBus(this.model, "mouse-out", () => this._onMouseOutProdPlanAlert());
  }

  get productionSimulation() {
    return this.props.data;
  }

  get groups() {
    return this.props.groups;
  }

  get isSelected() {
    return this.model.selectedRecords.has(this.productionSimulation.id);
  }

  formatFloat(value) {
    return formatFloat(value, {
      digits: [false, this.productionSimulation.precision_digits],
    });
  }

  /**
   * Handles the click on replenish button. It will call action_replenish with
   * all the Ids present in the view.
   * @private
   * @param {Integer} id dw.production.plan.simulation Id.
   */
  _onClickReplenish(id) {
    this.model._actionReplenish([id]);
  }

  /**
   * Handles the click on product name. It will open the product form view
   * @private
   * @param {MouseEvent} ev
   */
  _onClickRecordLink(ev) {
    this.actionService.doAction({
      type: "ir.actions.act_window",
      res_model: ev.currentTarget.dataset.model,
      res_id: Number(ev.currentTarget.dataset.resId),
      views: [[false, "form"]],
      target: "current",
    });
  }

  /**
   * Handles the click on `min..max` or 'targeted stock' Event. It will open
   * a form view in order to edit a production schedule and update the
   * template on save.
   *
   * @private
   * @param {MouseEvent} ev
   * @param {Integer} id dw.production.plan.simulation Id.
   */
  _onClickEdit(ev, id) {
    this.model._editProduct(id);
  }

  /**
   * Handles the click on unlink button. A dialog ask for a confirmation and
   * it will unlink the product.
   * @private
   * @param {Object} id dw.production.plan.simulation Id.
   */
  _onClickUnlink(id) {
    this.model._unlinkProduct([id]);
  }

  _onClickOpenDetails(ev) {
    const dateStart = ev.target.dataset.date_start;
    const dateStop = ev.target.dataset.date_stop;
    const dateStr = this.model.data.dates[ev.target.dataset.date_index];
    const action = ev.target.dataset.action;
    const productionSimulationId = Number(
      ev.target.closest(".o_mps_content").dataset.id
    );

    this.model._actionOpenDetails(
      productionSimulationId,
      action,
      dateStr,
      dateStart,
      dateStop
    );
  }

  /**
   * Handles the change on a simulation cell.
   * @private
   * @param {Event} ev
   * @param {Object} productionSimulationId dw.production.plan.simulation Id.
   */
  _onChangeForecast(ev, productionSimulationId) {
    const dateIndex = parseInt(ev.target.dataset.date_index);
    const forecastQty = ev.target.value;
    if (forecastQty === "" || isNaN(forecastQty)) {
      ev.target.value = this.model._getOriginValue(
        productionSimulationId,
        dateIndex,
        "forecasted_demand_qty"
      );
    } else {
      this.model
        ._saveForecast(productionSimulationId, dateIndex, forecastQty)
        .then(
          () => {
            const inputSelector =
              'input[data-date_index="' + (dateIndex + 1) + '"]';

            const nextInput = this.forecastRow.el.querySelector(inputSelector);
            if (nextInput) {
              nextInput.select();
            }
          },
          () => {
            ev.target.value = this.model._getOriginValue(
              productionSimulationId,
              dateIndex,
              "forecasted_demand_qty"
            );
          }
        );
    }
  }

  // # region: @bislem: Mocked data inputs

  /**
   * Handles the change on a simulation cell Sale Objective Qty.
   * @private
   * @param {Event} ev
   * @param {Object} productionSimulationId dw.production.plan.simulation Id.
   */

  onChangeSalesObjectiveQty(ev, productionSimulationId) {
    const dateIndex = parseInt(ev.target.dataset.date_index);
    const saleObjQty = ev.target.value;
    if (saleObjQty === "" || isNaN(saleObjQty)) {
      ev.target.value = this.model._getOriginValue(
        productionSimulationId,
        dateIndex,
        "sale_objective_qty"
      );
    } else {
      this.model
        ._saveSalesObjectiveQty(productionSimulationId, dateIndex, saleObjQty)
        .then(
          () => {
            const inputSelector =
              'input[data-date_index="' + (dateIndex + 1) + '"]';
            const nextInput = this.salesObjRow.el.querySelector(inputSelector);
            if (nextInput) {
              nextInput.select();
            }
          },
          () => {
            ev.target.value = this.model._getOriginValue(
              productionSimulationId,
              dateIndex,
              "sale_objective_qty"
            );
          }
        );
    }
  }

  onChangeProductionObjectiveQty(ev, productionSimulationId) {
    const dateIndex = parseInt(ev.target.dataset.date_index);
    const prodObjQty = ev.target.value;
    if (prodObjQty === "" || isNaN(prodObjQty)) {
      ev.target.value = this.model._getOriginValue(
        productionSimulationId,
        dateIndex,
        "production_objective_qty"
      );
    } else {
      this.model
        ._saveProductionObjectiveQty(
          productionSimulationId,
          dateIndex,
          prodObjQty
        )
        .then(
          () => {
            const inputSelector =
              'input[data-date_index="' + (dateIndex + 1) + '"]';
            const nextInput = this.prodObjRow.el.querySelector(inputSelector);
            if (nextInput) {
              nextInput.select();
            }
          },
          () => {
            ev.target.value = this.model._getOriginValue(
              productionSimulationId,
              dateIndex,
              "production_objective_qty"
            );
          }
        );
    }
  }

  onChangePlannedProductionQty(ev, productionSimulationId) {
    const dateIndex = parseInt(ev.target.dataset.date_index);
    const plannedProdQty = ev.target.value;
    if (plannedProdQty === "" || isNaN(plannedProdQty)) {
      ev.target.value = this.model._getOriginValue(
        productionSimulationId,
        dateIndex,
        "planned_production_qty"
      );
    } else {
      this.model
        ._savePlannedProductionQty(
          productionSimulationId,
          dateIndex,
          plannedProdQty
        )
        .then(
          () => {
            const inputSelector =
              'input[data-date_index="' + (dateIndex + 1) + '"]';
            const nextInput = this.forecastRow.el.querySelector(inputSelector);
            if (nextInput) {
              nextInput.select();
            }
          },
          () => {
            ev.target.value = this.model._getOriginValue(
              productionSimulationId,
              dateIndex,
              "planned_production_qty"
            );
          }
        );
    }
  }

  onChangeSoldQty(ev, productionSimulationId) {
    const dateIndex = parseInt(ev.target.dataset.date_index);
    const soldQty = ev.target.value;
    if (soldQty === "" || isNaN(soldQty)) {
      ev.target.value = this.model._getOriginValue(
        productionSimulationId,
        dateIndex,
        "sold_qty"
      );
    } else {
      this.model._saveSoldQty(productionSimulationId, dateIndex, soldQty).then(
        () => {
          const inputSelector =
            'input[data-date_index="' + (dateIndex + 1) + '"]';
          const nextInput =
            this.salesHistoryRow.el.querySelector(inputSelector);
          if (nextInput) {
            nextInput.select();
          }
        },
        () => {
          ev.target.value = this.model._getOriginValue(
            productionSimulationId,
            dateIndex,
            "sold_qty"
          );
        }
      );
    }
  }
  onChangeBatchCount(ev, productionSimulationId) {
    const dateIndex = parseInt(ev.target.dataset.date_index);
    const batchCount = ev.target.value;
    if (batchCount === "" || isNaN(batchCount)) {
      ev.target.value = this.model._getOriginValue(
        productionSimulationId,
        dateIndex,
        "batch_count"
      );
    } else {
      this.model
        ._saveBatchCount(productionSimulationId, dateIndex, batchCount)
        .then(
          () => {
            const inputSelector =
              'input[data-date_index="' + (dateIndex + 1) + '"]';
            const nextInput =
              this.prodPlanBatchesRow.el.querySelector(inputSelector);
            if (nextInput) {
              nextInput.select();
            }
          },
          () => {
            ev.target.value = this.model._getOriginValue(
              productionSimulationId,
              dateIndex,
              "batch_count"
            );
          }
        );
    }
  }

  onChangeStockLevel(ev, productionSimulationId) {
    const dateIndex = parseInt(ev.target.dataset.date_index);
    const stockLevel = ev.target.value;
    if (stockLevel === "" || isNaN(stockLevel)) {
      ev.target.value = this.model._getOriginValue(
        productionSimulationId,
        dateIndex,
        "stock_level"
      );
    } else {
      this.model
        ._saveStockLevel(productionSimulationId, dateIndex, stockLevel)
        .then(
          () => {
            const inputSelector =
              'input[data-date_index="' + (dateIndex + 1) + '"]';
            const nextInput = this.forecastRow.el.querySelector(inputSelector);
            if (nextInput) {
              nextInput.select();
            }
          },
          () => {
            ev.target.value = this.model._getOriginValue(
              productionSimulationId,
              dateIndex,
              "stock_level"
            );
          }
        );
    }
  }

  onChangeNotes(ev, productionSimulationId) {
    const dateIndex = parseInt(ev.target.dataset.date_index);
    const notes = ev.target.value;
    this.model._saveNotes(productionSimulationId, dateIndex, notes).then(
      () => {
        const inputSelector =
          'input[data-date_index="' + (dateIndex + 1) + '"]';
        const nextInput = this.forecastRow.el.querySelector(inputSelector);
        if (nextInput) {
          nextInput.select();
        }
      },
      () => {
        ev.target.value = this.model._getOriginValue(
          productionSimulationId,
          dateIndex,
          "notes"
        );
      }
    );
  }

  // # endregion: @bislem: Mocked data inputs

  /**
   * Handles the quantity To Replenish change on a simulation cell.
   * @private
   * @param {Event} ev
   * @param {Object} productionSimulationId dw.production.plan.simulation Id.
   */
  _onChangeToReplenish(ev, productionSimulationId) {
    const dateIndex = parseInt(ev.target.dataset.date_index);
    const replenishQty = ev.target.value;
    if (replenishQty === "" || isNaN(replenishQty)) {
      ev.target.value = this.model._getOriginValue(
        productionSimulationId,
        dateIndex,
        "replenish_qty"
      );
    } else {
      this.model
        ._saveToReplenish(productionSimulationId, dateIndex, replenishQty)
        .then(
          () => {
            const inputSelector =
              'input[data-date_index="' + (dateIndex + 1) + '"]';
            const nextInput = this.replenishRow.el.querySelector(inputSelector);
            if (nextInput) {
              nextInput.select();
            }
          },
          () => {
            ev.target.value = this.model._getOriginValue(
              productionSimulationId,
              dateIndex,
              "replenish_qty"
            );
          }
        );
    }
  }

  async _onClickForecastReport() {
    const action = await this.orm.call(
      "product.product",
      "action_product_forecast_report",
      [[this.productionSimulation.id]]
    );
    action.context = {
      active_model: "product.product",
      active_id: this.productionSimulation.product_id[0],
      warehouse_id:
        this.productionSimulation.warehouse_id &&
        this.productionSimulation.warehouse_id[0],
    };
    return this.actionService.doAction(action);
  }

  _onClickAutomaticMode(ev, productionSimulationId) {
    const dateIndex = parseInt(ev.target.dataset.date_index);
    this.model._removeQtyToReplenish(productionSimulationId, dateIndex);
  }

  _onFocusInput(ev) {
    ev.target.select();
  }

  _onMouseOverProdPlanAlert(ev) {
    const productionSimulationId = Number(
      ev.target.closest(".o_mps_content").dataset.id
    );
    const dateStart = ev.target.dataset.date_start;
    const dateStop = ev.target.dataset.date_stop;
    const dateIndex = parseInt(ev.target.dataset.date_index);

    const inputEl = this.prodObjRow.el.querySelector(
      'input[data-date_index="' + dateIndex + '"]'
    );

    if (inputEl) {
      inputEl.classList.add("o_prod_sim_hover");
      inputEl.classList.add("flash-pop");
    }
  }

  _onMouseOutProdPlanAlert(ev) {
    const productionSimulationId = Number(
      ev.target.closest(".o_mps_content").dataset.id
    );
    const dateStart = ev.target.dataset.date_start;
    const dateStop = ev.target.dataset.date_stop;
    const dateIndex = parseInt(ev.target.dataset.date_index);

    const inputEl = this.prodObjRow.el.querySelector(
      'input[data-date_index="' + dateIndex + '"]'
    );

    if (inputEl) {
      inputEl.classList.remove("o_prod_sim_hover");
      inputEl.classList.remove("flash-pop");
    }
  }

  _onClickProdPlanBatchesNotes(ev) {
    this.formVals = {};

    const productionSimulationId = Number(
      ev.target.closest(".o_mps_content").dataset.id
    );

    const dateStart = ev.target.dataset.date_start;
    const dateStop = ev.target.dataset.date_stop;
    const dateIndex = parseInt(ev.target.dataset.date_index);
    const dateStr = this.model.data.dates[dateIndex];

    const notes = ev.target.dataset.notes;
    const op = notes ? "Edit " : "Add ";

    this.formVals = {
      id: productionSimulationId,
      dateIndex: dateIndex,
      dateStart: dateStart,
      dateStop: dateStop,
      title: op + dateStr + " notes",
      headerTitle: "Period: " + dateStr,
      modalPeriodText: "Period: " + dateStr,
      batch_count: parseFloat(ev.target.dataset.batch_count),
      eff_planned_production_batches: parseFloat(
        ev.target.dataset.eff_planned_production_batches
      ),
      notes: notes,
    };

    let prodPlanBatchesEl = document.getElementById("production-plan-batches");
    let suggProdPlanBatchesEl = document.getElementById(
      "suggested-production-plan-batches"
    );

    document.getElementById("prodPlanBatchNotesModalHeadTitle").textContent =
      this.formVals.title;
    document.getElementById("modalPeriodText").textContent =
      this.formVals.modalPeriodText;
    prodPlanBatchesEl.textContent =
      this.formVals.eff_planned_production_batches;
    suggProdPlanBatchesEl.textContent = this.formVals.batch_count;
    document.getElementById("notes").value = notes;
    document.getElementById("notes").textContent = notes;

    // Color the greatest value in green and the other in red
    if (
      parseFloat(prodPlanBatchesEl.textContent) >=
      parseFloat(suggProdPlanBatchesEl.textContent)
    ) {
      prodPlanBatchesEl.classList.add("text-success");
      suggProdPlanBatchesEl.classList.add("text-danger");
      prodPlanBatchesEl.classList.remove("text-danger");
      suggProdPlanBatchesEl.classList.remove("text-success");
    } else {
      suggProdPlanBatchesEl.classList.add("text-success");
      prodPlanBatchesEl.classList.add("text-danger");
      suggProdPlanBatchesEl.classList.remove("text-danger");
      prodPlanBatchesEl.classList.remove("text-success");
    }

    $("#prodPlanBatchNotesModal").modal("show");
  }

  async saveProdPlanBatchesNotes(ev) {
    const notesEl = document.getElementById("notes");

    const notes = notesEl.value;

    await this.model
      ._saveProductionPlanBatchesNotes(
        this.formVals.id,
        this.formVals.dateIndex,
        this.formVals.dateStart,
        this.formVals.dateStop,
        notes
      )
      .then((result) => {
        this.formVals.notes = notes;

        var notesNotif = this.notificationService.add(
          _t(this.formVals.title + " successful"),
          {
            title: _t(this.formVals.title + " successful"),
            type: "success",
          }
        );
        setTimeout(notesNotif, 3000);
      })
      .catch((err) => {
        var notesNotif = this.notificationService.add(
          _t(this.formVals.title + " failed"),
          {
            title: _t(this.formVals.title + " failed"),
            type: "danger",
          }
        );
        setTimeout(notesNotif, 3000);
      });

    $("#prodPlanBatchNotesModal").modal("hide");
  }

  _onMouseOverProdPlanBatchesNotes(ev) {
    const productionSimulationId = Number(
      ev.target.closest(".o_mps_content").dataset.id
    );
    const dateStart = ev.target.dataset.date_start;
    const dateStop = ev.target.dataset.date_stop;
    const dateIndex = parseInt(ev.target.dataset.date_index);

    const inputEl = this.prodObjRow.el.querySelector(
      'input[data-date_index="' + dateIndex + '"]'
    );

    if (inputEl) {
      inputEl.classList.add("o_prod_sim_hover");
      inputEl.classList.add("flash-pop");
    }
  }

  _onMouseOutProdPlanBatchesNotes(ev) {
    const productionSimulationId = Number(
      ev.target.closest(".o_mps_content").dataset.id
    );
    const dateStart = ev.target.dataset.date_start;
    const dateStop = ev.target.dataset.date_stop;
    const dateIndex = parseInt(ev.target.dataset.date_index);

    const inputEl = this.prodObjRow.el.querySelector(
      'input[data-date_index="' + dateIndex + '"]'
    );

    if (inputEl) {
      inputEl.classList.remove("o_prod_sim_hover");
      inputEl.classList.remove("flash-pop");
    }
  }

  _onMouseOverCapacityAlert(ev) {
    const productionSimulationId = Number(
      ev.target.closest(".o_mps_content").dataset.id
    );
    const dateStart = ev.target.dataset.date_start;
    const dateStop = ev.target.dataset.date_stop;
    const dateIndex = parseInt(ev.target.dataset.date_index);

    const el = this.suggProdPlanRow.el.querySelector(
      'span[data-date_index="' + dateIndex + '"]'
    );

    if (el) {
      const divEl = el.closest(".span-group");
      if ("text-danger" in divEl.classList) {
        divEl.classList.remove("text-danger");
      }
      divEl.classList.add("flash-pop");
    }
  }

  _onMouseOutCapacityAlert(ev) {
    const productionSimulationId = Number(
      ev.target.closest(".o_mps_content").dataset.id
    );
    const dateStart = ev.target.dataset.date_start;
    const dateStop = ev.target.dataset.date_stop;
    const dateIndex = parseInt(ev.target.dataset.date_index);

    const el = this.suggProdPlanRow.el.querySelector(
      'span[data-date_index="' + dateIndex + '"]'
    );

    if (el) {
      const divEl = el.closest(".span-group");
      divEl.classList.remove("flash-pop");
    }
  }

  toggleSelection(ev, productionSimulationId) {
    try {
      this.model.toggleRecordSelection(productionSimulationId);
    } catch (error) {
      console.error(error);
    }
  }
}

ProductionPlanSimulatorLine.template =
  "dw_production_plan_simulator.ProductionPlanSimulatorLine";
ProductionPlanSimulatorLine.components = {
  CheckBox,
};
