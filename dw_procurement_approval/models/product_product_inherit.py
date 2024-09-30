# -*- coding:utf-8 -*-

from odoo import fields, models, api, _
from datetime import date


class DwProductTemplate(models.Model):
    _inherit = 'product.product'

    def _prepare_market_line(self):
        vals_dict = [
            (0, 0, {'product_id': self.id})]
        return vals_dict

    def _prepare_market(self):
        return {
            'company_id': self.company_id.id if self.company_id else False,
            'for_approval': True,
            "market_line_ids": self._prepare_market_line()
        }

    def action_launch_market(self):
        market_list = []
        DwMarket = self.env['procurement.market.dw']
        for rec in self:
            market_list.append(rec._prepare_market())
        DwMarket.create(market_list)
