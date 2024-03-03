/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
//import { BomOverviewControlPanel } from "../bom_overview_control_panel/mrp_bom_overview_control_panel";
//import { BomOverviewTable } from "../bom_overview_table/mrp_bom_overview_table";

const { Component, EventBus, onWillStart, useSubEnv, useState } = owl;

export class PlanOverviewComponent extends Component {
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");

        this.variants = [];
        this.warehouses = [];
        this.showVariants = false;
        this.uomName = "";
        this.extraColumnCount = 0;
        this.unfoldedIds = new Set();

        this.state = useState({
            showOptions: {
                uom: false,
                availabilities: true,
                costs: true,
                operations: true,
                leadTimes: true,
                attachments: false,
            },
            currentWarehouse: null,
            currentVariantId: null,
            bomData: {},
            bomQuantity: null,
        });

        useSubEnv({
            overviewBus: new EventBus(),
        });

        onWillStart(async () => {
            await this.getWarehouses();
            await this.initBomData();
        });
    }
}