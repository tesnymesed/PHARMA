from odoo import fields, models, _, api
from odoo import Command


class DwMarketAssign(models.TransientModel):
    _name = "procurement.market.dw.assign.wizard"

    approval_id = fields.Many2one("procurement.supplier.approval", string="approval")
    supplier_id = fields.Many2one('res.partner', string="Supplier", related="approval_id.supplier_id",
                                  domain='[("is_supplier","=", True)]'
                                  )
    product_id = fields.Many2one(
        'product.product',
        store=True,
        domain=['|', '|', ('need_approval', '=', True), ('categ_id.need_approval', '=', True),
                ('product_tmpl_id.need_approval', '=', True), ('purchase_ok', '=', True)],
        related="approval_id.product_id"
    )
    market_id = fields.Many2one('procurement.market.dw', string='Market')
    market_ids = fields.Many2many('procurement.market.dw', string='Market', compute="_compute_market_ids")

    @api.depends('market_id')
    def _compute_market_ids(self):
        market = self.env['procurement.market.dw']
        for record in self:
            a = market.search([('supplier_ids', 'in', self.supplier_id.id)])
            record.market_ids = market.search(
                [('for_approval', '=', True), ('product_ids', 'in', self.product_id.id),
                 ('supplier_ids', 'in', self.supplier_id.id)])

    def action_market_assign_confirm(self):
        self.market_id.write({'approval_ids': [Command.link(self.approval_id.id)], })
        self.approval_id.write({'market_ids': [Command.link(self.market_id.id)], })
