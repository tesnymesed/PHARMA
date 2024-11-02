
from odoo import models, api, fields


class SampleLineRequest(models.Model):
    _name = 'sample.request.lines'
    _description = 'Simple Line Request'

    product_id = fields.Many2one('product.product',string='Product')
    product_quantity = fields.Float(string="Quantity",digits='Product Unit of Measure')
    uom_id = fields.Many2one(comodel_name='uom.uom',string="Unit of Measure")
    simple_request_id = fields.Many2one('sample.request',string='Simple Request')
    lot_id = fields.Many2one('stock.lot', 'Lot/Serial Number',ddomain="[('product_id', '=', product_id)]", check_company=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company,)