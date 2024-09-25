from odoo import fields, models, _, api
from odoo import Command


class DwAttributeMarket(models.TransientModel):
    _name = "dw.homologate.market.wizard.line"

    supplier_id = fields.Many2one("res.partner", String="Supplier", domain='[("is_supplier","=", True)]',
                                  check_company=True, required=1)

class DwAttributeMarket(models.TransientModel):
    _name = "dw.homologate.market.wizard"

    line_id = fields.Many2one("procurement.market.dw.line", "Market")

    def prepare_approval_values(self, market_id, product_id, supplier_id, qty):
        return {
            'name': 'New',
            'market_ids': [Command.link(market_id.id)],
            'product_id': product_id.id,
            'supplier_id': supplier_id.id,
            'qty': qty,
        }

    def action_confirm(self):
        self.line_id.market_id.write({"state": "approval_consultation"})

    def action_create_approval_confirm(self):
        market_id = self.line_id.market_id

        approval_data = [
            self.prepare_approval_values(market_id, line.product_id, supplier_id, line.quantity)
            for line in market_id.market_line_ids
            for supplier_id in line.supplier_ids
        ]
        new_approvals = self.env['procurement.supplier.approval'].create(approval_data)

        if new_approvals:
            market_id.write({'approval_ids': [Command.link(hom.id) for hom in new_approvals]})

        self.line_id.line_approval = True
        self.action_confirm()

    # def action_link_market_with_approval(self):