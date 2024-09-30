from odoo import fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'


    def button_validate(self):
        if self.picking_type_id.code == 'incoming':
            for move_id in self.move_ids:
                if not any(move_line.location_dest_id.location_transfer_limit_id.perform_transfer 
                        for move_line in move_id.move_line_ids):
                    raise UserError(f"The {move_id.product_id.name} could not be found in any transfer location.")
                    
        return super().button_validate()


    