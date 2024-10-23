from odoo import fields, models

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    dw_supplier_ref = fields.Char( string="Internal Reference")

    def _prepare_new_lot_vals(self):
        vals = super()._prepare_new_lot_vals()
        dw_supplier_ref=self.dw_supplier_ref
        if dw_supplier_ref:
            vals['ref'] = dw_supplier_ref
        return vals

