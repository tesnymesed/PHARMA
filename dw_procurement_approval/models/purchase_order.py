# -*- coding:utf-8 -*-

from odoo import fields, models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    market_id = fields.Many2one('procurement.market.dw', string='Market')
    approval_id = fields.Many2one('procurement.supplier.approval', string='approval')
    supplier_approval_ids = fields.Many2many(
        'res.partner',
        related="market_id.supplier_approval_ids"
    )

    @api.model
    def create(self, values):
        res = super(PurchaseOrder, self).create(values)
        if res.approval_id:
            res.approval_id.write({"purchase_id": res.id})
        return res
