from odoo import api, fields, models


class DwStockProductionLot(models.Model):
    _inherit = 'stock.lot'

    dw_num_supplier = fields.Char(string="Ref Fournisseur")


class DwStockLocation(models.Model):
    _inherit = 'stock.location'

    dw_is_quarantine = fields.Boolean(string="Is Quarantine")


class DwStockPicking(models.Model):
    _inherit = 'stock.quant'

    ref = fields.Char(
        related='lot_id.ref'
    )


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _search_picking_for_assignation_domain(self):
        domain = super()._search_picking_for_assignation_domain()
        domain.append(("dw_picking_to_merge", "=", False))
        return domain


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    dw_picking_to_merge = fields.Boolean(default=False)
    dw_route_no_origin = fields.Boolean(default=False, compute="compute_dw_route_no_origin")

    # @api.depends("move_ids_without_package", "state")
    def compute_dw_route_no_origin(self):
        for record in self:
            if any(line.procure_method in ['make_to_order'] and not line.move_orig_ids for line in
                   record.move_ids_without_package):
                record.dw_route_no_origin = True
            else:
                record.dw_route_no_origin = False

    def dw_recompute_state(self):
        self.ensure_one()
        lines_with_make_to_order_no_origin = self.move_ids_without_package.filtered(
            lambda line: line.procure_method in ['make_to_order'] and not line.move_orig_ids)
        lines_with_make_to_order_no_origin.sudo().write({"procure_method": 'make_to_stock'})
        self.sudo().action_assign()
