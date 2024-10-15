from odoo.exceptions import UserError
from odoo import _,models

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        for picking in self:
            picking_type = picking.picking_type_id.code if picking.picking_type_id else False
            if picking_type in ['incoming', 'mrp_operation']:
                self._check_lot_compliance(picking.move_ids, 'location_dest_id')
                
            elif picking_type == 'outgoing':
                self._check_lot_compliance(picking.move_ids, 'location_id')
                
            elif picking_type == 'internal':
                self._check_internal_transfer(picking.move_ids)

        return super(StockPicking, self).button_validate()

    def _check_lot_compliance(self, move_ids, location_field):
        for move_id in move_ids:
            for move_line in move_id.move_line_ids:
                location = getattr(move_line, location_field)
                if location.perform_transfer:
                    if move_id.product_id and move_id.product_id.requires_lot_compliance_check:
                        self._validate_lot_conformity(move_line.lot_id, move_id.product_id)

    def _check_internal_transfer(self, move_ids):
        for move_id in move_ids:
            for move_line in move_id.move_line_ids:
                if not move_line.location_id.perform_transfer or not move_line.location_dest_id.perform_transfer:
                    if move_id.product_id and move_id.product_id.requires_lot_compliance_check:
                        self._validate_lot_conformity(move_line.lot_id, move_id.product_id)

    def _validate_lot_conformity(self, lot, product):
        if lot.lot_status != 'conform':
            raise UserError(_(f"The transfer for {product.name} cannot be performed for non-conform lot: {lot.name}"))
