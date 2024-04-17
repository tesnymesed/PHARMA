from odoo import models, api, fields


class ProductCategory(models.Model):
    _inherit = "product.category"

    homologue = fields.Boolean(
        'homologué',
        default=False
    )
