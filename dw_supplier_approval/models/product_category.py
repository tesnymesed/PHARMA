from odoo import models, api, fields


class ProductCategory(models.Model):
    _inherit = "product.category"

    need_approval = fields.Boolean(
        'approval required',
        default=False
    )
