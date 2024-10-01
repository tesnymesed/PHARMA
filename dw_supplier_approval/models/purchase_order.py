# -*- coding:utf-8 -*-
from odoo import models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        for order in self:
            for line in order.order_line:
                product = line.product_id
                partner_id = line.partner_id
                approvals = product.mapped('approval_ids').filtered(lambda approval: approval.state == 'approval' and approval.supplier_id.id == partner_id.id)

                if not approvals:
                    raise UserError(
                        f"The supplier {partner_id.name} is not approved for the product {product.name}.")

            return super().button_confirm()
