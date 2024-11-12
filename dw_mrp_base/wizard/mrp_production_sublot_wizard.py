from odoo import models, fields , _

class MrpProductionSublot(models.TransientModel):
    _name = "mrp.production.sublot"
    _description = "MRP Production Sublot Wizard"

    sublot_id = fields.Char(string="Sublot number")

    def action_cancel(self):
        return {'type':'ir.actions.act_window_close'}

    def action_confirmsublot(self):
        return {'type':'ir.actions.act_window_close'}
