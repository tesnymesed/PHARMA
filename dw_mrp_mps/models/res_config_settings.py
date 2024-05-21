# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    manufacturing_period_start = fields.Selection(related="company_id.manufacturing_period_start",
                                                  string="Manufacturing Period Start", readonly=False)

    dw_use_product_lead = fields.Boolean(string="Use Product Lead Time", config_parameter='dw_mrp.dw_use_product_lead')

    manufacturing_lead = fields.Float(related='company_id.manufacturing_lead', string="Manufacturing Lead Time",
                                      config_parameter='dw_mrp.manufacturing_lead',
                                      readonly=False)

    # @api.model
    # def get_values(self):
    #     res = super(ResConfigSettings, self).get_values()
    #
    #     params = self.env['ir.config_parameter'].sudo()
    #     dw_use_product_lead = params.get_param('dw_mrp.dw_use_product_lead', default=False)
    #     res.update({
    #         'dw_mrp.dw_use_product_lead': bool(dw_use_product_lead),
    #     })
    #
    #     manufacturing_lead = params.get_param('dw_mrp.manufacturing_lead', default=0.0)
    #     res.update({
    #         'dw_mrp.manufacturing_lead': float_round(round(float(manufacturing_lead), 2), precision_digits=2),
    #     })
    #
    #     return res
    #
    # @api.model
    # def set_values(self):
    #     super(ResConfigSettings, self).set_values()
    #     IrgConfig = self.env['ir.config_parameter'].sudo()
    #
    #     IrgConfig.set_param("dw_mrp.dw_use_product_lead", self.dw_use_product_lead)
    #     IrgConfig.set_param("dw_mrp.manufacturing_lead", self.manufacturing_lead)

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
        # if bool(self.env['ir.config_parameter'].sudo().get_param('dw_mrp.dw_use_product_lead')):

    @api.onchange('use_manufacturing_lead')
    def _onchange_use_manufacturing_lead(self):
        if not self.use_manufacturing_lead:
            self.manufacturing_lead = 0.0
            self.dw_use_product_lead = False
            # TODO: force 0.0 upon disabling this option

