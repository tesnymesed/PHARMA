from odoo import models, fields


class DWMrpProductionBackorder(models.TransientModel):
    _name = "mrp.production.sublot"

    new_sublot = fields.Boolean(string="New Sublot", default=True)
    sublot_id = fields.Char(string="Sublot Number")

    def action_backorer(self):
        return {'type': 'ir.actions.act_window_close'}

    def action_skip_backorder(self):
        return {'type': 'ir.actions.act_window_close'}

    def action_close(self):
        return {'type': 'ir.actions.act_window_close'}
