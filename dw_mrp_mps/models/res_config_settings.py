# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    manufacturing_period_start = fields.Selection(related="company_id.manufacturing_period_start",
                                                  string="Manufacturing Period Start", readonly=False)

    @api.onchange('manufacturing_period_start')
    def _compute_manufacturing_period_settings(self):
        if self.manufacturing_period_start == 'year_start':
            self.manufacturing_period = 'month'
            self.manufacturing_period_to_display = 12

