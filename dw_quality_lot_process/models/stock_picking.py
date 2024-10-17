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
            if move_id.product_id and move_id.product_id.requires_lot_compliance_check:
                for move_line in move_id.move_line_ids:
                    location = getattr(move_line, location_field)
                    if not location.perform_transfer:
                        if location.must_check_lot_compiliance :
                            autorized_lot_status = location.lot_status_for_tranfer_ids.mapped('name')
                            self._validate_lot_conformity(autorized_lot_status,move_line.lot_id, move_id.product_id)

    def _check_internal_transfer(self, move_ids):
        for move_id in move_ids:
            if move_id.product_id and move_id.product_id.requires_lot_compliance_check:
                for move_line in move_id.move_line_ids:
                    if move_line.location_id and not move_line.location_id.perform_transfer :
                        if  move_line.location_id.must_check_lot_compiliance :
                            autorized_lot_status=move_line.location_id.lot_status_for_tranfer_ids.mapped('name')
                            self._validate_lot_conformity(autorized_lot_status,move_line.lot_id, move_id.product_id)
                    if move_line.location_dest_id and not move_line.location_dest_id.perform_transfer:
                        if move_line.location_dest_id.must_check_lot_compiliance:
                            autorized_lot_status = move_line.location_dest_id.lot_status_for_tranfer_ids.mapped('name')
                            self._validate_lot_conformity(autorized_lot_status,move_line.lot_id, move_id.product_id)
                        

    def _validate_lot_conformity(self, autorized_lot_status,lot, product):
        if lot.lot_status not in autorized_lot_status:
            raise UserError(_(f"The transfer for {product.name} cannot be performed for lot : {lot.lot_status} {lot.name}"))
