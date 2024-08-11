# -*- coding:utf-8 -*-

from odoo import fields, models, api


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    market_id = fields.Many2one('dw.market', string='Market')
