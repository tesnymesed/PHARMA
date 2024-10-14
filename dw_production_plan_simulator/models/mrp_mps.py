# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json

from odoo import fields, models


class DWMrpProductionSchedule(models.Model):
    _name = 'mrp.production.schedule'
    _inherit = ['mrp.production.schedule', 'dw.pharma.resource.access.mixin']

    _sql_constraints = [
        ('warehouse_product_ref_uniq', 'unique (dw_simulation_ok, warehouse_id, product_id)',
         'The combination of warehouse and product must be unique!'),
    ]

    # def _get_global_context(self, action_id=None):
    #     # context = super().with_context(action_type='client')._get_global_context(action_id)
    #     context = super(DWMrpProductionSchedule, self)._get_global_context(action_id, action_type='client')
    #     return context

