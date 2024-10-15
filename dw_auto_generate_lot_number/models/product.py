# -*- coding:utf-8 -*-

from odoo import fields, models, api, _

class DwProduct(models.Model):
    _inherit = 'product.template'

    auto_generate_lot_number = fields.Boolean(string='Auto Generate Lot Number', default=False)
    lot_code = fields.Char(string='Lot Short Code')
    counter = fields.Integer()
    sequence_size = fields.Integer(default="5", string='Sequence Length')

class StockLot(models.Model):
    _inherit = 'stock.move.line'

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        if res and res.product_id and res.product_id.auto_generate_lot_number:
            res.lot_name = generate_sequence(res.product_id.lot_code, res.product_id.sequence_size, res.product_id.counter)
            res.product_id.counter += 1
        return res

def generate_sequence(prefix, sequence_size, seq):
    # Format the sequence number with leading zeros based on the sequence_size
    formatted_seq = f"{seq:0{sequence_size}d}"
    # Return the final formatted string
    return f"{prefix}{formatted_seq}"

