# -*- coding:utf-8 -*-
from odoo import _, api, fields, models


class DwResCompany(models.Model):
    _inherit = 'res.company'

    dw_mrp_roadmap_sequence_id = fields.Many2one(
        comodel_name='ir.sequence', string='Mrp Roadmap Sequence',
        domain="['|',('company_id', '=', company_id),('company_id', '=', False)]",
        help='Select the default Sequence for the MRP Roadmap')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    dw_mrp_roadmap_sequence_id = fields.Many2one(
        comodel_name='ir.sequence', string='Mrp Roadmap Sequence',
        related='company_id.dw_mrp_roadmap_sequence_id',
        readonly=False,
        domain="['|',('company_id', '=', company_id),('company_id', '=', False)]",
        help='Select the default Sequence for the MRP Roadmap')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        params = self.env['ir.config_parameter'].sudo()
        dw_mrp_roadmap_sequence_id = params.get_param('dw_mrp_roadmap_sequence_id', default=False)
        res.update(
            dw_mrp_roadmap_sequence_id=int(dw_mrp_roadmap_sequence_id) if dw_mrp_roadmap_sequence_id else False,
        )
        return res

    @api.model
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        IrgConfig = self.env['ir.config_parameter'].sudo()
        IrgConfig.set_param("dw_mrp_roadmap_sequence_id",
                            self.dw_mrp_roadmap_sequence_id.id if self.dw_mrp_roadmap_sequence_id else False)
