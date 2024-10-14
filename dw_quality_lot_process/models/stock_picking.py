from odoo import _, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        for picking in self:
            picking_type = picking.picking_type_id.code if picking.picking_type_id else False
            # in case picking type is outgoing transfer or a fabrication
            if picking_type in ['outgoing', 'mrp_operation']:

                for move_id in picking.move_ids:
                    if move_id.product_id and move_id.product_id.requires_lot_compliance_check == True: # for each line of picking check if lot check is set to true
                        for lot in move_id.lot_ids : #in case lot check is true, loop over the lots
                            if lot.lot_status !='conform': #if any lot status is not conform raise error
                                raise UserError(_(f"The transfer for {move_id.product_id.name} cannot be performed for non-conform lot: {lot.name}"))
                        if move_id.move_line_ids : #in case there is move lines 
                            for move_line in move_id.move_line_ids :  
                                if move_line.lot_id.lot_status != 'conform' : #check if for every line of move_id it's lot status is set to conform otherwise raise error
                                    raise UserError(_(f"The transfer for {move_id.product_id.name} cannot be performed for non-conform lot: {move_line.lot_id.name}"))
            #in case picking type is an internal transfer
            elif picking_type =='internal':
                for move_id in picking.move_ids : # loop over each move_id of picking
                    if move_id.location_dest_id and move_id.location_dest_id.perform_transfer== False or\
                        move_id.location_id and move_id.location_id.perform_transfer== False : #if we can not perform a transfer in location or location destination 
                        for lot in move_id.lot_ids : #loop over lots of move_id 
                            if lot.lot_status!='conform':  #if the lot status is conform
                                if move_id.product_id.requires_lot_compliance_check==True: #the product should be lot compliance checked true otherwise raise error
                                    raise UserError(_(f"The transfer for the product {move_id.product_id.name} cannot be performed in the lot : {lot.name}"))
                    # in case move_line_ids exists over loop it
                    if move_id.move_line_ids :
                        for line in move_id.move_line_ids :

                            if line.location_dest_id.perform_transfer ==False or \
                                line.location_id.perform_transfer ==False : #if source or destination locations of line can not perform a transfer 
                                if line.lot_id.lot_status!='conform': #and the lot status of line is conform
                                    if line.product_id.requires_lot_compliance_check==True: #and line product lot compliance is false raise error
                                        raise UserError(_(f"The transfer for the product {move_id.product_id.name} cannot be performed in the lot : {line.lot_id.name}"))
            
        return super().button_validate()