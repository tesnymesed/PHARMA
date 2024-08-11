# from odoo import fields, models, api, _
#
#
# class DwProduct(models.Model):
#     _inherit = 'product.product'
#
#     dw_purchase_lead = fields.Float("Product Purchase Lead Time", default=0.0,
#                                     related='product_tmpl_id.dw_purchase_lead',
#                                     help="Lead days for each purchase operation (Used in MPS).")
