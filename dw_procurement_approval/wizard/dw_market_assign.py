from odoo import fields, models, _, api
from odoo import Command


class DwMarketAssign(models.TransientModel):
    _name = "procurement.market.dw.assign.wizard"

    approval_id = fields.Many2one("procurement.supplier.approval", string="approval")
    supplier_id = fields.Many2one('res.partner', string="Supplier", related="approval_id.supplier_id")
    company_id = fields.Many2one( string="Company", related="approval_id.company_id")
    product_id = fields.Many2one(
        related="approval_id.product_id"
    )
    market_id = fields.Many2one('procurement.market.dw', string='Market', check_company=True,
                                domain='[("approval_ids","not in", approval_id)]')

    def action_market_assign_confirm(self):
        self.market_id.write({'approval_ids': [Command.link(self.approval_id.id)], })
        self.approval_id.write({'market_ids': [Command.link(self.market_id.id)], })
