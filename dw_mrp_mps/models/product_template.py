from odoo import fields, models


class DwProductTemplate(models.Model):
    _inherit = 'product.template'

    dw_purchase_lead = fields.Float(
        "Purchase Lead Time", default=0.0, help="Lead days for each purchase operation (Used in MPS).")
