from odoo import fields, models, _, api
from odoo import Command


class DwMarketAssign(models.TransientModel):
    _name = "dw.market.assign.wizard"

    homologation_id = fields.Many2one("dw.homologation", string="Homologation")
    supplier_id = fields.Many2one('res.partner', string="Supplier", related="homologation_id.supplier_id",
                                  domain='[("is_supplier","=", True)]'
                                  )
    product_id = fields.Many2one(
        'product.product',
        store=True,
        domain=['|', '|', ('homologue', '=', True), ('categ_id.homologue', '=', True),
                ('product_tmpl_id.homologue', '=', True), ('purchase_ok', '=', True)],
        related="homologation_id.product_id"
    )
    market_id = fields.Many2one('dw.market', string='Market')
    market_ids = fields.Many2many('dw.market', string='Market', compute="_compute_market_ids")

    @api.depends('market_id')
    def _compute_market_ids(self):
        market = self.env['dw.market']
        for record in self:
            a = market.search([('supplier_ids', 'in', self.supplier_id.id)])
            record.market_ids = market.search(
                [('dw_for_homologation', '=', True), ('product_ids', 'in', self.product_id.id),
                 ('supplier_ids', 'in', self.supplier_id.id)])

    def action_market_assign_confirm(self):
        self.market_id.write({'homologation_ids': [Command.link(self.homologation_id.id)], })
        self.homologation_id.write({'market_ids': [Command.link(self.market_id.id)], })
