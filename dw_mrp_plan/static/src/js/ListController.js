odoo.define("dw_mrp_plan.ButtonInList", function (require) {
  "use strict";

  const ListController = require("web.ListController");
  const core = require("web.core");

  const includeDict = {
    // render button is an Odoo function that manages buttons in the view manager
    renderButtons: function () {
      this._super.apply(this, arguments);
      // check that this button will only appear in my model
      if (this.modelName === "product.mrp.plan") {
        const self = this;
        // Get the button object in order to attribute to it a behavior
        const coa_button = this.$buttons.find(".dw_list_button_update");
        coa_button.on("click", function (event) {
          self.o_button_click();
        });
      }
    },

    o_button_click: function (e) {
      // Get the active id passed in the context
      const active_id = this.controlPanelProps.action.context.active_id;
      // Use rpc method to access my backend function
      const self = this;
      this._rpc({
        model: "product.mrp.plan",
        method: "action_update",
        args: [active_id],
      }).then(function () {
        // This function is used to reload only data in the table not the entire screen
        self.trigger_up("reload");
      });
    },
  };

  ListController.include(includeDict);
});
