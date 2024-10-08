/** @odoo-module **/
import { useService, useBus } from "@web/core/utils/hooks";
import { formatFloat } from "@web/core/utils/numbers";
import { Component, useRef, onPatched, useState } from "@odoo/owl";

export default class ProductionPlanBatchesNotesEditor extends Component {
  setup() {
    this.state = useState({
      isModalVisible: false,
    });
  }
  get productionSimulation() {
    return this.props.data;
  }

  toggleModal() {
    this.state.isModalVisible = !this.state.isModalVisible;
  }
}

ProductionPlanBatchesNotesEditor.template =
  "dw_production_plan_simulator.ProductionNotesEditorTemplate";
