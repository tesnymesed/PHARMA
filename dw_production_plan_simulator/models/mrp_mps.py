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


    max_to_replenish_qty = fields.Float(
        'Maximum to Replenish', default=999999999999999,
        help="The maximum replenishment you would like to launch for each period in the MPS. Note that if the demand is higher than that amount, the remaining quantity will be transferred to the next period automatically.")

    forecast_target_qty = fields.Float(
        'Safety Stock Target', related='product_id.dw_safety_stock_qty', readonly=False,
        store=True, help="This is the minimum free stock you want to keep for that product at all times.")

    # def _get_global_context(self, action_id=None):
    #     # context = super().with_context(action_type='client')._get_global_context(action_id)
    #     context = super(DWMrpProductionSchedule, self)._get_global_context(action_id, action_type='client')
    #     return context

