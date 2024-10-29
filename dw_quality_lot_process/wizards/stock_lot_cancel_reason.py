from odoo import models, fields, _
from odoo.exceptions import UserError

class StockLotCancelWizard(models.TransientModel):
    _name = 'stock.lot.cancel.wizard'
    _description = 'Stock Lot Cancel Wizard'

    reason_id = fields.Many2one('stock.lot.cancel.reason', string='Reason')
    note = fields.Text(string='Note')
    lot_id = fields.Many2one('stock.lot', string='Stock Lot', required=True)
    status = fields.Selection([
        ('not_conform', 'Not Conform'),
        ('blocked', 'Blocked'),
        ('cancelled', 'Cancelled')],string="Lot Failed Status")
    check_quality_id = fields.Many2one(
        'quality.check',
        string='Check Quality',
        )
    fail_location_id = fields.Many2one(
        'stock.location',string = 'Location'
        )
    non_conform_qty = fields.Float(string='Quantity Non-Conform')
    non_conform_lot = fields.Char()
    def _create_history_record(self,with_reason=False):
        '''This function creates record in stock.lot.history
        the parameter with_reason is set to false in case the user does not provide a reason
        if it's set to true a new record is created with reason and note if exit'''

        history_vals = {
            'lot_id': self.lot_id.id,
            'user_id': self.env.user.id,
            'change_date': fields.Datetime.now(),
            'previous_status': self.lot_id.lot_status,
            'new_status': self.status if self.status else False,
            'reason_id': self.reason_id.id if with_reason else False,
            'note' : self.note if with_reason else '',
        }
        self.env['stock.lot.history'].sudo().create(history_vals)
    
    def action_cancel_reason_lot(self):
        if self.check_quality_id :
            if self.fail_location_id :
                self.check_quality_id.picking_id.location_dest_id = self.fail_location_id.id
            if  self.non_conform_qty !=0 :
                conform_qty = self.check_quality_id.picking_lot_quantity-self.non_conform_qty

                if conform_qty >=0 :
                    move_id = self.check_quality_id.picking_id.move_line_ids.filtered(
                        lambda move :move.product_id.id==self.check_quality_id.product_id.id and 
                        move.lot_id.id==self.check_quality_id.lot_id.id and 
                        move.location_id.id==self.check_quality_id.location_id.id)

                    move_id.quantity=conform_qty
                    quant = self.check_quality_id.lot_id.quant_ids.filtered(
                        lambda quant:quant.location_id.id==self.check_quality_id.location_id.id)
                    quant.quantity=conform_qty

                    if self.non_conform_lot :
                        lot = {
                            'name': self.non_conform_lot,
                            'is_child':True,
                            'parent_lot_id':self.check_quality_id.lot_id.id,
                            'product_id':self.check_quality_id.product_id.id,
                            'company_id':self.env.company.id,
                        }
                        lot_id = self.env['stock.lot'].sudo().create(lot)
                        quant = {
                            'location_id':self.check_quality_id.location_id.id,
                            'lot_id':lot_id.id,
                            'product_id':lot_id.product_id.id,
                            'quantity':self.non_conform_qty,
                            'company_id':self.env.company.id
                        }
                        self.env['stock.quant'].sudo().create(quant)
                else :
                    raise UserError(_(f"Non Conform quantity should not be grater than lot quantity"))

            self.check_quality_id.do_fail()
        if self.lot_id and self.lot_id.lot_quarantine_status !='analyzed' :
            self.lot_id.action_set_analyzed()    
        self._create_history_record(with_reason=True)
        self.lot_id.lot_status = self.status if self.status else False
        message = f"Lot cancelled. Reason: {self.reason_id.name if self.reason_id else 'No reason provided'}"
        self.lot_id.message_post(body=message)

        return True
    def action_cancel(self):
        return True
