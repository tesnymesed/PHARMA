# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    manufacturing_period_start = fields.Selection(related="company_id.manufacturing_period_start",
                                                  string="Manufacturing Period Start", readonly=False)

    dw_use_product_lead = fields.Boolean(string="Use Product Lead Time", config_parameter='mrp.dw_use_product_lead')

    @api.onchange('manufacturing_period_start')
    def _compute_manufacturing_period_settings(self):
        if self.manufacturing_period_start == 'year_start':
            self.manufacturing_period = 'month'
            self.manufacturing_period_to_display = 12

    # @api.depends('dw_use_product_lead')
    @api.onchange('dw_use_product_lead')
    def _onchange_dw_use_product_lead(self):
        if not self.dw_use_product_lead:
            pass
        # To get this parameter value use:
        # if bool(self.env['ir.config_parameter'].sudo().get_param('mrp.dw_use_product_lead')):

    @api.onchange('use_manufacturing_lead')
    def _onchange_use_manufacturing_lead(self):
        if not self.use_manufacturing_lead:
            self.manufacturing_lead = 0.0
            self.dw_use_product_lead = False
