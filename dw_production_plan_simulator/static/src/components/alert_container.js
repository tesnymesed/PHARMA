/** @odoo-module **/
import { useService, useBus } from "@web/core/utils/hooks";
import { formatFloat } from "@web/core/utils/numbers";
import { Component, useRef, onPatched, useState } from "@odoo/owl";

export default class ProductionPlanSimulationAlerts extends Component {

    setup() {
        this.state = useState({
        isModalVisible: false,
    });


    }

    toggleModal() {
        this.state.isModalVisible = !this.state.isModalVisible;
    }
}


ProductionPlanSimulationAlerts.template =
  "dw_production_plan_simulator.ProductionPlanSimulationAlertsTemplate";
