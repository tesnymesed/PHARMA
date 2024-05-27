/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { MasterProductionScheduleModel } from '@mrp_mps/models/master_production_schedule_model';
patch(MasterProductionScheduleModel.prototype, {
    async load(start_date_range='', end_date_range='') {
        this.data = await this.orm.call('mrp.production.schedule', 'dw_get_date_range', [start_date_range, end_date_range]);
        this.notify();
    }
});