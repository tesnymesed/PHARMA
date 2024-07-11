/** @odoo-module **/

import { CheckBox } from "@web/core/checkbox/checkbox";
import { useService, useBus } from "@web/core/utils/hooks";
import { formatFloat } from "@web/core/utils/numbers";
import { Component, useRef, onPatched } from "@odoo/owl";

export default class ProductionPlanSimulatorLine extends Component {
  setup() {
    this.actionService = useService("action");
    this.dialogService = useService("dialog");
    this.orm = useService("orm");
    this.model = this.env.model;
    this.forecastRow = useRef("forecastRow");
    this.replenishRow = useRef("replenishRow");

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

    useBus(this.model, "mouse-over", () => this._onMouseOverReplenish());
    useBus(this.model, "mouse-out", () => this._onMouseOutReplenish());
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

  _onMouseOverReplenish(ev) {
    const el = this.replenishRow.el.getElementsByClassName(
      "o_prod_sim_forced_replenish"
    );
    if (el && el[0]) {
      el[0].classList.add("o_prod_sim_hover");
    }
  }

  _onMouseOutReplenish(ev) {
    const el = this.replenishRow.el.getElementsByClassName("o_prod_sim_hover");
    if (el && el[0]) {
      el[0].classList.remove("o_prod_sim_hover");
    }
  }

  toggleSelection(ev, productionSimulationId) {
    this.model.toggleRecordSelection(productionSimulationId);
  }
}

ProductionPlanSimulatorLine.template = "mrp_mps.ProductionPlanSimulatorLine";
ProductionPlanSimulatorLine.components = {
  CheckBox,
};
