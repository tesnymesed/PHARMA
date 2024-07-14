from odoo import fields, models, _, api
from odoo import Command

class DwAttributeMarket(models.TransientModel):
    _name = "dw.homologate.market.wizard"

    line_id = fields.Many2one("dw.market.line", "Market")

    def prepare_homologation_values(self, market_id, product_id, supplier_id, qty):
        return {
            'name': 'New',
            'market_ids': [Command.link(market_id.id)],
            'product_id': product_id.id,
            'supplier_id': supplier_id.id,
            'qty': qty,
        }

    def action_confirm(self):
        market_id = self.line_id.market_id
        market_id.write({"state": "homologation_cosultation"})

    def action_create_homologation_confirm(self):
        market_id = self.line_id.market_id
        homologation = []
        for line in market_id.market_line_ids:
            for supplier_id in line.supplier_ids:
                homologation.append(
                    self.prepare_homologation_values(market_id, line.product_id, supplier_id, line.quantity))
        new_homologation = self.env['dw.homologation'].create(homologation)
        for hom in new_homologation:
         market_id.write({'homologation_ids':[Command.link(hom.id)]})
        self.line_id.line_homlogated = True
        # self.action_confirm()
