# -*- coding:utf-8 -*-
from odoo import  models
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        for order in self : 
            for line in order.order_line :
                product = line.product_id

                domain = [('supplier_id','=',order.partner_id.id),('product_id','=',product.id),('state','=','approval')]
                approvals = order.env['procurement.supplier.approval'].sudo().search(domain)
                if not approvals:
                    raise UserError(f"The supplier {order.partner_id.name} is not approved for the product {product.name}.")

            return super().button_confirm()
