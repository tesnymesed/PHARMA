from odoo import models, api, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    requires_lot_compliance_check = fields.Boolean(default=False,string='Requires Lot Compiliance Check')
