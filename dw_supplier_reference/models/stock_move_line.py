from odoo import fields, models

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    ref = fields.Char( string="Internal Reference")

    def _prepare_new_lot_vals(self):
        vals = super()._prepare_new_lot_vals()
        if self.ref:
            vals['ref'] = self.ref
        return vals

    @api.model
    def create(self, values):
        res = super().create(values)
        if res and res.ref:
            res.ref = self.ref
        return res
