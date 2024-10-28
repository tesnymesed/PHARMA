
from odoo import models, api, fields


class SampleLineRequest(models.Model):
    _name = 'sample.request.lines'
    _description = 'Simple Line Request'

    product_id = fields.Many2one('product.product',string='Product')
    product_uom_qty = fields.Float(string="Quantity",digits='Product Unit of Measure')
    product_uom = fields.Many2one(comodel_name='uom.uom',string="Unit of Measure")
    simple_request_id = fields.Many2one('sample.request',string='Simple Request')
    lot_id = fields.Many2one('stock.lot', string='Lot/Serial')