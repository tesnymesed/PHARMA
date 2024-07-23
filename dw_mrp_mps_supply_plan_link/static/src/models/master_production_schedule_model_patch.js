/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { MasterProductionScheduleModel } from "@mrp_mps/models/master_production_schedule_model";
import { useService } from "@web/core/utils/hooks";

import { _t } from "@web/core/l10n/translation";

patch(MasterProductionScheduleModel.prototype, {
  setup() {
    super.setup();
    this.notificationService = useService("notification");
  },
  /**
   
   */
  _createSupplyPlans(dateStart, dateStop) {
    console.log(
      "🚀 ~ _createSupplyPlans ~ this.data.production_schedule_ids:",
      this.data.production_schedule_ids,
      dateStart,
      dateStop
    );
    console.log("🚀 ~ _createSupplyPlans ~ this.domain:", this.domain);

    return this.mutex.exec(() => {
      this.orm
        .call("mrp.production.schedule", "create_supply_plans", [
          // productionScheduleId,
          this.data.production_schedule_ids,
        ])
        .then((res) => {
          console.log("🚀 ~ .then ~ res:", res);
          let supply_plan_ids = res[0];
          console.log("🚀 ~ .then ~ supply_plan_ids:", supply_plan_ids);
          try {
            let approved_ids = res[1];
            console.log("🚀 ~ .then ~ approved_ids:", approved_ids);
            if (approved_ids) {
              var approved_notif = this.notificationService.add(
                _t("Approved Supply Plans were detected"),
                {
                  title: _t("Approved Supply Plans"),
                  type: "success",
                }
              );
              setTimeout(approved_notif, 2000);
            }
          } catch (error) {
            console.error("Error handling approved IDs", error);
          }

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
              domain: [["supply_plan_id.id", "in", supply_plan_ids]],
              context: {
                group_by: ["state", "supply_plan_id", "product_id"],
                expand: true,
              },
              target: "current",
              search_view_id: false,
              filter: false,
            };
            // let _action = {
            //   name: _t("MRP Supply Plans"),
            //   type: "ir.actions.act_window",
            //   res_model: "dw.mrp.supply.plan",
            //   views: [
            //     [false, "tree"],
            //     [false, "form"],
            //   ],
            //   view_mode: "tree,form",
            //   target: "current",
            //   domain: [("id", "in", supply_plan_ids)],
            // };

            this.action.doAction(action);
          });
        })
        .catch((err) => {
          console.error(_t("Error opening supply plans"), err);
        });
    });
  },
});
