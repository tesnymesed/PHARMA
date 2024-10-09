# -*- coding: utf-8 -*-

from odoo import models


class DwMrpSimulationWorkCenter(models.Model):
    _name = 'mrp.workcenter'
    _inherit = ['mrp.workcenter', 'dw.pharma.resource.access.mixin']

    def create(self, vals):
        records = super().create(vals)
        for record in records:
            if not record.dw_simulation_ok:
                # vals['dw_simulation_ok'] = True
                cloned_records = super(DwMrpSimulationWorkCenter, self).with_context(dw_pharma_simulation=True).create(
                    vals)

        return records
