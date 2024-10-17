# -*- coding:utf-8 -*-

from odoo import fields, models, api, _

class DwProduct(models.Model):
    _inherit = 'product.template'

    auto_generate_lot_number = fields.Boolean(string='Auto Generate Lot Number',store=True,readonly=False, default=False, related='dw_pharma_family_id.auto_generate_lot_number')
    lot_code = fields.Char(string='Lot Short Code', store=True, default=False,readonly=False, related='dw_pharma_family_id.lot_code')
    sequence_size = fields.Integer( string='Sequence Length', store=True, readonly=False, related='dw_pharma_family_id.sequence_size')
    counter = fields.Integer()