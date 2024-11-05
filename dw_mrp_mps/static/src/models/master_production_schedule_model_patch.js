/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { MasterProductionScheduleModel } from "@mrp_mps/models/master_production_schedule_model";
patch(MasterProductionScheduleModel.prototype, {
  async load(
    domain,
    offset,
    limit,
    start_date_range = "",
    end_date_range = ""
  ) {
    if (domain !== undefined) {
      this.domain = domain;
    }
    if (offset !== undefined) {
      this.offset = offset;
    }
    if (limit !== undefined) {
      this.limit = limit;
    }
    this.data = await this.orm.call(
      "mrp.production.schedule",
      "get_mps_view_state",
      [this.domain, this.offset, this.limit, start_date_range, end_date_range]
    );
    this.notify();
  },
  /**
   * Save the notes (text).
   * @private
   * @param {Integer} productionScheduleId mrp.production.schedule Id.
   * @param {String} dateStart period to save
   * @param {String} dateStop period to save
   * @param {String} notes The new notes (text)
   * @return {Promise}
   */
  _saveNotes(productionScheduleId, dateStart, dateStop, notes) {
    return this.mutex.exec(() => {
      this.orm
        .call("mrp.production.schedule", "set_notes", [
          productionScheduleId,
          dateStart,
          dateStop,
          notes,
        ])
        .then(() => {
          return this.reload(productionScheduleId);
        });
    });
  },
  /**
   * Save the decision ID (int).
   * @private
   * @param {Integer} productionScheduleId mrp.production.schedule Id.
   * @param {String} dateStart period to save
   * @param {String} dateStop period to save
   * @param {String} decisionId The new decision ID (int)
   * @return {Promise}
   */
  _saveDecision(productionScheduleId, dateStart, dateStop, decisionId) {
    return this.mutex.exec(() => {
      this.orm
        .call("mrp.production.schedule", "set_decision", [
          productionScheduleId,
          dateStart,
          dateStop,
          decisionId,
        ])
        .then(() => {
          return this.reload(productionScheduleId);
        });
    });
  },
});
