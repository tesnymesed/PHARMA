from odoo import models, api, fields


class ProductCategory(models.Model):
    _inherit = "product.category"

    is_final_product = fields.Boolean(
        'Final Product Category',
        default=False
    )
