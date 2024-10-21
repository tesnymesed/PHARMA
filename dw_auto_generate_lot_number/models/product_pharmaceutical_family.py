# -*- coding:utf-8 -*-

from odoo import fields, models, api, _

class ProductPharmaceuticalFamily(models.Model):
    _inherit = 'product.pharmaceutical.family'

    lot_code = fields.Char(string='Lot Short Code')
    auto_generate_lot_number = fields.Boolean(string='Auto Generate Lot Number', default=False)
    sequence_size = fields.Integer(default="5", string='Sequence Length')