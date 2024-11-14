from odoo import models, fields, api


class DWMrpProductionBackorder(models.TransientModel):
    _inherit = 'mrp.production.backorder'
    _description = "Wizard to mark as done or create back order, with Sublot Options"

    new_sublot = fields.Boolean(string="New Sublot", default=True)
    sublot_id = fields.Char(string="Sublot Number")

    bom_id = fields.Many2one('mrp.bom',)
    tracking_type = fields.Selection(related="bom_id.tracking_type")

    mrp_production_backorder_line_ids = fields.One2many(
        'mrp.production.backorder.line',
        'mrp_production_backorder_id',
        string="Backorder Confirmation Lines"
    )
    mrp_production_ids = fields.Many2many('mrp.production')

    show_backorder_lines = fields.Boolean(
        "Show backorder lines",
        compute="_compute_show_backorder_lines"
    )

    @api.depends('mrp_production_backorder_line_ids')
    def _compute_show_backorder_lines(self):
        for wizard in self:
            wizard.show_backorder_lines = len(wizard.mrp_production_backorder_line_ids) > 1

    def action_close_mo(self):
        ctx = dict(self.env.context)
        always_backorder_mo_ids = ctx.pop('always_backorder_mo_ids', [])
        return self.mrp_production_ids.with_context(
            ctx, skip_backorder=True, mo_ids_to_backorder=always_backorder_mo_ids
        ).button_mark_done()

    def action_backorder(self):
        ctx = dict(self.env.context)
        ctx.pop('default_mrp_production_ids', None)
        always_backorder_mo_ids = ctx.pop('always_backorder_mo_ids', [])
        mo_ids_to_backorder = self.mrp_production_backorder_line_ids.filtered(
            lambda l: l.to_backorder
        ).mrp_production_id.ids + always_backorder_mo_ids
        return self.mrp_production_ids.with_context(
            ctx, skip_backorder=True, mo_ids_to_backorder=mo_ids_to_backorder, lot_id=self.sublot_id
        ).button_mark_done()
