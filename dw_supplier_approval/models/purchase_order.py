
# -*- coding:utf-8 -*-

from odoo import fields, models,api
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    market_id = fields.Many2one('dw.market', string = 'Market')
    homologation_id = fields.Many2one('dw.homologation', string='Homologation')
    supplier_homologuer_ids = fields.Many2many(
        'res.partner',
        related="market_id.supplier_homologuer_ids"
    )
    @api.model
    def create(self, values):
        res = super(PurchaseOrder, self).create(values)
        if res.homologation_id:
         res.homologation_id.write({"purchase_id": res.id})
        return res



