from odoo import _, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'


    def button_validate(self):
        for picking in self:
            for move_id in picking.move_ids:
                # Check if the transfer can be performed at the move_id level
                if move_id.location_id and move_id.location_id.location_transfer_limit_id and not move_id.location_id.location_transfer_limit_id.perform_transfer:
                    raise UserError(_(f"The {move_id.product_id.name} could not be performed in the transfer location."))

                # Check if the transfer can be performed at the move_line_id level
                if move_id.move_line_ids:
                    if not any(move_line.location_id.location_transfer_limit_id.perform_transfer for move_line in move_id.move_line_ids):
                        raise UserError(_(f"The {move_id.product_id.name} could not be performed in any transfer location for its move lines."))

        return super().button_validate()


    