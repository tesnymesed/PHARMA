from odoo import models, fields


class DwProductTemplate(models.Model):
    _inherit = 'product.template'
    dw_safety_stock_qty = fields.Float(string='Safety Stock Quantity', default=1.0,
                                       help="Minimum free stock we want to keep for the product at all times.")


class DWProductProduct(models.Model):
    _inherit = 'product.product'

    dw_safety_stock_qty = fields.Float(string='Safety Stock Quantity', related='product_tmpl_id.dw_safety_stock_qty',
                                       readonly=False, store=True,
                                       help="Minimum free stock we want to keep for the product at all times.")
