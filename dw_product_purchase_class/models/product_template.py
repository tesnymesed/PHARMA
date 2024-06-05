from odoo import fields, models


class DwProductTemplate(models.Model):
    _inherit = 'product.template'

    dw_product_class_id = fields.Many2one('dw.product.purchase.class', string="Product Purchase Class")
