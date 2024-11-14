from odoo import fields, api, models, _


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    lot_dates_set = fields.Boolean(default=False
    )
    use_expiration_date = fields.Boolean(
        related='product_id.use_expiration_date'
    )
    extra_cost = fields.Float(readonly=False, compute="_compute_extra_cost", store=1)


    tracking_type = fields.Selection(related='bom_id.tracking_type',store=1)

    @api.depends('lot_producing_id', 'lot_producing_id.expiration_date')
    def _compute_lot_dates_set(self):
        for record in self:
            if record.lot_producing_id and record.lot_producing_id.expiration_date:
                record.lot_dates_set = True
            else:
                record.lot_dates_set = False

    def action_cancel(self):
        super().action_cancel()
        if self.lot_producing_id:
            self.lot_producing_id.action_archive()

    def action_set_lot_dates(self):
        form_view = self.env.ref('dw_mrp_base.mrp_production_lot_wizard_form')

        action = {
            'name': _('Set Production lot dates'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production.lot',
            'target': 'new'
        }

        action['views'] = [
            (form_view.id, 'form')
        ]
        action['view_mode'] = 'form'
        action['domain'] = [('production_id', '=', self.id)]
        action['context'] = {'default_production_id': self.id, 'default_lot_id': self.lot_producing_id.id}
        return action

    # def button_mark_done(self):
    #     if not self.lot_dates_set and self.lot_producing_id and self.product_id.use_expiration_date:
    #         raise ValidationError(_("Your produced lot doesn't have an expiration date, please correct it !"))
    #     return super(MrpProduction, self).button_mark_done()

    @api.onchange("product_id", "bom_id")
    def onchange_dw_location_component(self):
        bom_id = self.bom_id
        if bom_id and bom_id.dw_force_mrp_config and bom_id.dw_location_component_id:
            self.location_src_id = bom_id.dw_location_component_id

    @api.depends("bom_id")
    def _compute_extra_cost(self):
        for prod in self:
            prod.extra_cost = prod.bom_id.dw_majoration if prod.bom_id else 0


    def _get_backorder_mo_vals(self):
        res = super()._get_backorder_mo_vals()

        if self.env.context.get('lot_id', False):
            lot = self.env['stock.lot'].create({
                'name': self.env.context.get('lot_id', False),
                'product_id': self.product_id.id,
            })
            res['lot_producing_id'] = lot.id
        return res

    def action_addsublot(self):
        return {
            'name': _('Wizard Upload Workforce'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production.sublot',
            'context': {'default_mrp_production_id': self.id},
            'view_mode': 'form',
            'target': 'new',
        }