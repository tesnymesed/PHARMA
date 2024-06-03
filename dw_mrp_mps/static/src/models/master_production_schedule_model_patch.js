/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { MasterProductionScheduleModel } from '@mrp_mps/models/master_production_schedule_model';
patch(MasterProductionScheduleModel.prototype, {
    async load(domain, offset, limit, start_date_range='', end_date_range='') {
        if (domain !== undefined) {
            this.domain = domain;
        }
        if (offset !== undefined) {
            this.offset = offset;
        }
        if (limit !== undefined) {
            this.limit = limit;
        }
        this.data = await this.orm.call('mrp.production.schedule', 'get_mps_view_state', [this.domain, this.offset, this.limit, start_date_range, end_date_range]);
        this.notify();
    }
});