/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { MasterProductionScheduleModel } from "@mrp_mps/models/master_production_schedule_model";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(MasterProductionScheduleModel.prototype, {
  setup() {
    super.setup();
    this.notificationService = useService("notification");
  },
  /**
   
   */
  _createSupplyPlans(dateStart, dateStop) {
    function createSupplyPlans() {
      console.log("🚀 ~ _createSupplyPlans ~ this.domain:", this.domain);

      return this.mutex.exec(() => {
        this.orm
          .call("mrp.production.schedule", "create_supply_plans", [
            // productionScheduleId,
            this.data.production_schedule_ids,
          ])
          .then((supply_plan_ids) => {
            console.log("🚀 ~ .then ~ supply_plan_ids:", supply_plan_ids);

            this.mutex.exec(() => {
              let action = {
                name: _t("MRP Supply Plans"),
                type: "ir.actions.act_window",
                res_model: "dw.mrp.product.supply.plan",
                views: [
                  [false, "tree"],
                  [false, "form"],
                ],
                view_mode: "tree,form",
                domain: [["id", "in", supply_plan_ids]],
                context: {
                  group_by: ["product_id"],
                  expand: true,
                },
                target: "current",
                search_view_id: false,
                filter: false,
              };
              this.action.doAction(action);
            });
          })
          .catch((err) => {
            console.error(_t("Error opening supply plans"), err);
          });
      });
    }

    const body =
      this.data.production_schedule_ids.length > 1
        ? _t("Are you sure you want to create Supply Plans for these records?")
        : _t("Are you sure you want to create Supply Plans for this record?");
    this.dialog.add(ConfirmationDialog, {
      body: body,
      title: _t("Confirmation"),
      confirm: createSupplyPlans.bind(this),
    });
  },
});
