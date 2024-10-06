from odoo import _, models, fields



class ProductProduct(models.Model):
    _inherit = 'product.product'

    restrict_transfer = fields.Boolean(default=False)
