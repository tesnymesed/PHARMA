/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { Mutex } from "@web/core/utils/concurrency";
import { EventBus } from "@odoo/owl";

export class ProductionPlanSimulatorModel extends EventBus {
  constructor(params, services) {
    super();
    this.domain = [];
    this.offset = 0;
    this.limit = false;
    this.startDate;
    this.endDate;
    this.params = params;
    this.orm = services.orm;
    this.action = services.action;
    this.dialog = services.dialog;
    this.selectedRecords = new Set();
    this.mutex = new Mutex();
  }

  saveDateRange(companyId, startDate, endDate) {
    return this.mutex.exec(() => {
      this.orm
        .call("res.company", "set_prod_sim_date_range", [
          companyId,
          startDate,
          endDate,
        ])
        .then((res) => {
          console.log("Updated Date Range");
        });
    });
  }

  saveSalesDateRange(companyId, startDate, endDate) {
    return this.mutex.exec(() => {
      this.orm
        .call("res.company", "set_prod_sim_sales_date_range", [
          companyId,
          startDate,
          endDate,
        ])
        .then((res) => {
          console.log("Updated Sales Date Range");
        });
    });
  }

  calculateSalesAverage(companyId, startDate, endDate) {
    return this.mutex.exec(() => {
      this.orm
        .call("dw.production.plan.simulation", "calculate_sales_average", [
          companyId,
          startDate,
          endDate,
        ])
        .then((res) => {
          console.log("Updated sales average ", res);
        })
        .catch((error) => {
          console.error("error", error);
        });
    });
  }

  async load(domain, offset, limit, startDate, endDate) {
    if (domain !== undefined) {
      this.domain = domain;
    }
    if (offset !== undefined) {
      this.offset = offset;
    }
    if (limit !== undefined) {
      this.limit = limit;
    }
    if (startDate !== undefined) {
      this.startDate = startDate;
    }
    if (endDate !== undefined) {
      this.endDate = endDate;
    }

    this.data = await this.orm.call(
      "dw.production.plan.simulation",
      "get_prod_simulator_view_state",
      [this.domain, this.offset, this.limit, this.startDate, this.endDate]
    );
    this.notify();
  }

  async reload(productionSimulationId) {
    return await this.orm
      .call("dw.production.plan.simulation", "get_impacted_schedule", [
        productionSimulationId,
        this.domain,
      ])
      .then((productionSimulationIds) => {
        productionSimulationIds.push(productionSimulationId);
        console.log("reload with ", productionSimulationId);

        return this.orm.call(
          "dw.production.plan.simulation",
          "get_production_simulation_view_state",
          [productionSimulationIds]
        );
      })
      .then((production_simulation_ids) => {
        for (var i = 0; i < production_simulation_ids.length; i++) {
          const index = this.data.production_simulation_ids.findIndex(
            (ps) => ps.id === production_simulation_ids[i].id
          );
          if (index >= 0) {
            this.data.production_simulation_ids.splice(
              index,
              1,
              production_simulation_ids[i]
            );
          } else {
            this.data.production_simulation_ids.push(
              production_simulation_ids[i]
            );
          }
        }
        this.orm
          .call("dw.production.plan.simulation", "get_workcenter_capacities", [
            productionSimulationId,
            this.data.production_simulation_ids,
          ])
          .then((workcentersCapacities) => {
            console.log(
              "🚀 ~ ProductionPlanSimulatorModel ~ .then ~ workcentersCapacities:",
              workcentersCapacities
            );
            this.data.workcenter_capacities = workcentersCapacities;
          })
          .catch((err) => {
            console.log(err);
          });
        console.log(
          "this.data.production_simulation_ids",
          this.data.production_simulation_ids
        );
        console.log(
          "🚀 ~ ProductionPlanSimulatorModel ~ .then ~ this.data.workcenter_capacities:",
          this.data.workcenter_capacities
        );

        this.notify();
      });
  }

  notify() {
    this.unselectAll();
    this.trigger("update");
  }

  /**
   * Make an rpc to replenish the different schedules passed as arguments.
   * If the procurementIds list is empty, it replenish all the schedules under
   * the current domain. Reload the content after the replenish in order to
   * display the new simulation cells to run.
   * @private
   * @param {Integer[]} productionSimulationIds dw.production.plan.simulation ids to
   * replenish.
   * @return {Promise}
   */
  _actionReplenish(productionSimulationIds, basedOnLeadTime = false) {
    this.mutex.exec(() => {
      return this.orm
        .call("dw.production.plan.simulation", "action_replenish", [
          productionSimulationIds,
          basedOnLeadTime,
        ])
        .then(() => {
          if (productionSimulationIds.length === 1) {
            this.reload(productionSimulationIds[0]);
          } else {
            this.load();
          }
        });
    });
  }

  replenishAll() {
    this.orm
      .search("dw.production.plan.simulation", this.domain)
      .then((ids) => {
        this._actionReplenish(ids, true);
      });
  }

  replenishSelectedRecords() {
    this._actionReplenish(Array.from(this.selectedRecords), false);
  }

  _;

  /**
   * Save the forecasted quantity and reload the current schedule in order
   * to update its To Replenish quantity and its safety stock (current and
   * future period). Also update the other schedules linked by BoM in order
   * to update them depending the indirect demand.
   * @private
   * @param {Integer} productionSimulationId dw.production.plan.simulation Id.
   * @param {Integer} dateIndex period to save (column number)
   * @param {Float} forecastQty The new forecasted quantity
   * @return {Promise}
   */
  _saveForecast(productionSimulationId, dateIndex, forecastQty) {
    return this.mutex.exec(() => {
      this.orm
        .call("dw.production.plan.simulation", "set_forecast_qty", [
          productionSimulationId,
          dateIndex,
          forecastQty,
        ])
        .then(() => {
          return this.reload(productionSimulationId);
        });
    });
  }

  // # region: @bislem: Mocked data inputs

  /**
   * Save the forecasted quantity and reload the current schedule in order
   * to update its To Replenish quantity and its safety stock (current and
   * future period). Also update the other schedules linked by BoM in order
   * to update them depending the indirect demand.
   * @private
   * @param {Integer} productionSimulationId dw.production.plan.simulation Id.
   * @param {Integer} dateIndex period to save (column number)
   * @param {Float} forecastQty The new forecasted quantity
   * @return {Promise}
   */
  _saveSalesObjectiveQty(productionSimulationId, dateIndex, saleObjQty) {
    return this.mutex.exec(() => {
      this.orm
        .call("dw.production.plan.simulation", "set_sales_objective_qty", [
          productionSimulationId,
          dateIndex,
          saleObjQty,
        ])
        .then(() => {
          return this.reload(productionSimulationId);
        });
    });
  }

  /**
   * Save the production objective quantity and reload the current schedule to update dependent data.
   * @private
   * @param {Integer} productionSimulationId dw.production.plan.simulation Id.
   * @param {Integer} dateIndex period to save (column number)
   * @param {Float} productionObjectiveQty The new production objective quantity
   * @return {Promise}
   */
  _saveProductionObjectiveQty(
    productionSimulationId,
    dateIndex,
    productionObjectiveQty
  ) {
    return this.mutex.exec(() => {
      this.orm
        .call("dw.production.plan.simulation", "set_production_objective_qty", [
          productionSimulationId,
          dateIndex,
          productionObjectiveQty,
        ])
        .then(() => {
          return this.reload(productionSimulationId);
        });
    });
  }

  /**
   * Save the planned production quantity and reload the current schedule to update dependent data.
   * @private
   * @param {Integer} productionSimulationId dw.production.plan.simulation Id.
   * @param {Integer} dateIndex period to save (column number)
   * @param {Float} plannedProductionQty The new planned production quantity
   * @return {Promise}
   */
  _savePlannedProductionQty(
    productionSimulationId,
    dateIndex,
    plannedProductionQty
  ) {
    return this.mutex.exec(() => {
      this.orm
        .call("dw.production.plan.simulation", "set_planned_production_qty", [
          productionSimulationId,
          dateIndex,
          plannedProductionQty,
        ])
        .then(() => {
          return this.reload(productionSimulationId);
        });
    });
  }

  /**
   * Save the sold quantity and reload the current schedule to update dependent data.
   * @private
   * @param {Integer} productionSimulationId dw.production.plan.simulation Id.
   * @param {Integer} dateIndex period to save (column number)
   * @param {Float} soldQty The new sold quantity
   * @return {Promise}
   */
  _saveSoldQty(productionSimulationId, dateIndex, soldQty) {
    return this.mutex.exec(() => {
      this.orm
        .call("dw.production.plan.simulation", "set_sold_qty", [
          productionSimulationId,
          dateIndex,
          soldQty,
        ])
        .then(() => {
          return this.reload(productionSimulationId);
        });
    });
  }

  /**
   * Save the batch count and reload the current schedule to update dependent data.
   * @private
   * @param {Integer} productionSimulationId dw.production.plan.simulation Id.
   * @param {Integer} dateIndex period to save (column number)
   * @param {Float} soldQty The new sold quantity
   * @return {Promise}
   */
  _saveBatchCount(productionSimulationId, dateIndex, batchCount) {
    return this.mutex.exec(() => {
      this.orm
        .call("dw.production.plan.simulation", "set_batch_count", [
          productionSimulationId,
          dateIndex,
          batchCount,
        ])
        .then(() => {
          return this.reload(productionSimulationId);
        });
    });
  }

  /**
   * Save the stock level and reload the current schedule to update dependent data.
   * @private
   * @param {Integer} productionSimulationId dw.production.plan.simulation Id.
   * @param {Integer} dateIndex period to save (column number)
   * @param {Float} stockLevel The new stock level
   * @return {Promise}
   */
  _saveStockLevel(productionSimulationId, dateIndex, stockLevel) {
    return this.mutex.exec(() => {
      this.orm
        .call("dw.production.plan.simulation", "set_stock_level", [
          productionSimulationId,
          dateIndex,
          stockLevel,
        ])
        .then(() => {
          return this.reload(productionSimulationId);
        });
    });
  }

  /**
   * Save the notes (text) and reload the current schedule to update dependent data.
   * @private
   * @param {Integer} productionSimulationId dw.production.plan.simulation Id.
   * @param {Integer} dateIndex period to save (column number)
   * @param {String} notes The new notes (text)
   * @return {Promise}
   */
  _saveNotes(productionSimulationId, dateStart, dateStop, notes) {
    return this.mutex.exec(() => {
      this.orm
        .call("dw.production.plan.simulation", "set_notes", [
          productionSimulationId,
          dateStart,
          dateStop,
          notes,
        ])
        .then(() => {
          // return this.reload(productionSimulationId);
        });
    });
  }

  /**
   * Save the decision ID (int).
   * @private
   * @param {Integer} productionScheduleId dw.production.plan.simulation Id.
   * @param {String} dateStart period to save
   * @param {String} dateStop period to save
   * @param {String} decisionId The new decision ID (int)
   * @return {Promise}
   */
  _saveDecision(productionScheduleId, dateStart, dateStop, decisionId) {
    return this.mutex.exec(() => {
      this.orm
        .call("dw.production.plan.simulation", "set_decision", [
          productionScheduleId,
          dateStart,
          dateStop,
          decisionId,
        ])
        .then(() => {
          // return this.reload(productionScheduleId);
        });
    });
  }

  // # endregion: @bislem: Mocked data inputs

  /**
   * Open the dw.production.plan.simulation form view in order to create the record.
   * Once the record is created get its state and render it.
   * @private
   * @return {Promise}
   */
  _createProducts(state) {
    this.mutex.exec(() => {
      return this.orm
        .call("dw.production.plan.simulation", "create_product_simulations", [
          state.currentCompanyId,
        ])
        .then((res) => {
          this.load([["company_id", "=", state.currentCompanyId]]);
          return this.data;
          //                if (productionSimulationIds.length === 1) {
          //                    this.reload(productionSimulationIds[0]);
          //                } else {
          //                    this.load();
          //                }
        })
        .catch((error) => {
          console.error("error", error);
        });
    });
  }

  /**
   * Open the dw.production.plan.simulation form view in order to create the MPS records.
   * Once the record is created get its state and render it.
   * @private
   * @return {Promise}
   */
  _createMPSEntries(companyId, productionSimulations) {
    return this.mutex.exec(() => {
      return this.orm
        .call(
          "dw.production.plan.simulation",
          "create_mps_from_plan_simulations",
          [companyId, productionSimulations]
        )
        .then((res) => {
          console.log("🚀 ~ ProductionPlanSimulatorModel ~ .then ~ res:", res);
          // this.load([["company_id", "=", state.currentCompanyId]]);
          // return this.data;
          //                if (productionSimulationIds.length === 1) {
          //                    this.reload(productionSimulationIds[0]);
          //                } else {
          //                    this.load();
          //                }

          this.notify();
          return res;
        })
        .catch((error) => {
          console.error("error", error);
          return error;
        });
    });
  }

  _openMPS(state) {
    this.mutex.exec(() => {
      this.action.doAction(
        {
          name: "Materials Availability",
          type: "ir.actions.client",
          tag: "mrp_mps_client_action",
          target: "fullscreen",
          domain: [["company_id", "=", state.currentCompanyId]],
          params: {
            company: state.currentCompanyId,
            startDate: state.startDate,
            endDate: state.endDate,
          },
          context: {
            company: state.currentCompanyId,
            startDate: state.startDate,
            endDate: state.endDate,
          },

          //          views: [[false, "form"]],
          //          res_model: "dw.production.plan.simulation",
          //          res_id: productionSimulationId,
        }
        //        {
        //          onClose: () => this.reload(productionSimulationId),
        //        }
      );
    });
  }

  /**
   * Open the dw.production.plan.simulation form view in order to edit the record.
   * Once the record is edited get its state and render it.
   * @private
   * @param {Integer} productionSimulationId dw.production.plan.simulation Id.
   */
  _editProduct(productionSimulationId) {
    this.mutex.exec(() => {
      this.action.doAction(
        {
          name: "Edit Production Plan Simulation",
          type: "ir.actions.act_window",
          res_model: "dw.production.plan.simulation",
          views: [[false, "form"]],
          target: "new",
          res_id: productionSimulationId,
        },
        {
          onClose: () => this.reload(productionSimulationId),
        }
      );
    });
  }

  /**
   * Open the dw.production.plan.simulation form view in order to edit the record.
   * Once the record is edited get its state and render it.
   * @private
   * @param {Integer} productionSimulationId dw.production.plan.simulation Id.
   */
  _editWorkCenter(productionSimulationId) {
    this.mutex.exec(() => {
      this.action.doAction(
        {
          name: "Edit Production Plan Simulation",
          type: "ir.actions.act_window",
          res_model: "dw.production.plan.simulation",
          views: [[false, "form"]],
          target: "new",
          res_id: productionSimulationId,
        },
        {
          onClose: () => this.reload(productionSimulationId),
        }
      );
    });
  }

  /**
   * Unlink the production schedule and remove it from the DOM. Use a
   * confirmation dialog in order to avoid a mistake from the user.
   * @private
   * @param {Integer[]} productionSimulationIds dw.production.plan.simulation Ids.
   * @return {Promise}
   */
  _unlinkProduct(productionSimulationIds) {
    function doIt() {
      this.mutex.exec(async () => {
        return Promise.all(
          productionSimulationIds.map((id) =>
            this.orm.unlink("dw.production.plan.simulation", [id])
          )
        ).then(() => {
          for (const productionSimulationId of productionSimulationIds) {
            const index = this.data.production_simulation_ids.findIndex(
              (ps) => ps.id === productionSimulationId
            );
            this.data.production_simulation_ids.splice(index, 1);
          }
          this.notify();
        });
      });
    }
    const body =
      productionSimulationIds.length > 1
        ? _t("Are you sure you want to delete these records?")
        : _t("Are you sure you want to delete this record?");
    this.dialog.add(ConfirmationDialog, {
      body: body,
      title: _t("Confirmation"),
      confirm: doIt.bind(this),
    });
  }

  unlinkSelectedRecord() {
    return this._unlinkProduct(Array.from(this.selectedRecords));
  }

  /**
   *
   * @param {Integer} productionSimulationId dw.production.plan.simulation Id
   * @param {String} action name of the action to be undertaken
   * @param {String} dateStr name of the period
   * @param {String} dateStart start date of the period
   * @param {String} dateStop end date of the period
   * @return {Promise}
   */
  _actionOpenDetails(
    productionSimulationId,
    action,
    dateStr,
    dateStart,
    dateStop
  ) {
    this.mutex.exec(() => {
      return this.orm
        .call("dw.production.plan.simulation", action, [
          productionSimulationId,
          dateStr,
          dateStart,
          dateStop,
        ])
        .then((action) => {
          return this.action.doAction(action);
        });
    });
  }

  /**
   * Save the quantity To Replenish and reload the current schedule in order
   * to update it's safety stock and quantity in future period. Also mark
   * the cell with a blue background in order to show that it was manually
   * updated.
   * @private
   * @param {Integer} productionSimulationId dw.production.plan.simulation Id.
   * @param {Integer} dateIndex period to save (column number)
   * @param {Float} replenishQty The new quantity To Replenish
   * @return {Promise}
   */
  _saveToReplenish(productionSimulationId, dateIndex, replenishQty) {
    return this.mutex.exec(() => {
      this.orm
        .call("dw.production.plan.simulation", "set_replenish_qty", [
          productionSimulationId,
          dateIndex,
          replenishQty,
        ])
        .then(() => {
          return this.reload(productionSimulationId);
        });
    });
  }

  /**
   * Remove the manual change of replenishQty and load the suggested value.
   * @private
   * @param {Integer} productionSimulationId dw.production.plan.simulation Id.
   * @param {Integer} dateIndex period to save (column number)
   * @return {Promise}
   */
  _removeQtyToReplenish(productionSimulationId, dateIndex) {
    return this.mutex.exec(() => {
      this.orm
        .call("dw.production.plan.simulation", "remove_replenish_qty", [
          productionSimulationId,
          dateIndex,
        ])
        .then(() => {
          return this.reload(productionSimulationId);
        });
    });
  }

  _getOriginValue(productionSimulationId, dateIndex, inputName) {
    return this.data.production_simulation_ids.find(
      (ps) => ps.id === productionSimulationId
    ).product_plan_sim_ids[dateIndex][inputName];
  }

  /**
   * Save the company settings and hide or display the rows.
   * @private
   * @param {Object} values {field_name: field_value}
   */
  _saveCompanySettings(values) {
    +this.mutex.exec(() => {
      this.orm.write("res.company", [this.data.company_id], values).then(() => {
        this.load();
      });
    });
  }

  mouseOverAlert() {
    this.trigger("mouse-over");
  }

  mouseOutAlert() {
    this.trigger("mouse-out");
  }

  selectAll() {
    this.data.production_simulation_ids.map(({ id }) =>
      this.selectedRecords.add(id)
    );
  }

  unselectAll() {
    this.selectedRecords.clear();
  }

  toggleRecordSelection(productionSimulationId) {
    if (this.selectedRecords.has(productionSimulationId)) {
      this.selectedRecords.delete(productionSimulationId);
    } else {
      this.selectedRecords.add(productionSimulationId);
    }
    this.trigger("update");
  }

  toggleSelection() {
    if (
      this.selectedRecords.size === this.data.production_simulation_ids.length
    ) {
      this.unselectAll();
    } else {
      this.selectAll();
    }
    this.trigger("update");
  }
}
