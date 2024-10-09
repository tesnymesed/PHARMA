from odoo import models, fields, api

class StockLotCancelWizard(models.TransientModel):
    _name = 'stock.lot.cancel.wizard'
    _description = 'Stock Lot Cancel Wizard'

    reason_id = fields.Many2one('stock.lot.cancel.reason', string='Reason')  # Reason is optional
    note = fields.Text(string='Note')  # Note is optional
    lot_id = fields.Many2one('stock.lot', string='Stock Lot', required=True)
    
    def _create_history_record(self,with_reason=False):
        '''This function creates record in stock.lot.history
        the parameter with_reason is set to false in case the user does not provide a reason
        if it's set to true a new record is created with reason and note if exit'''

        history_vals = {
            'lot_id': self.lot_id.id,
            'user_id': self.env.user.id,
            'change_date': fields.Datetime.now(),
            'previous_status': self.lot_id.lot_status,
            'new_status': 'cancelled',
            'reason_id': self.reason_id.id if with_reason else False,
            'note' : self.note if with_reason else '',
        }
        self.env['stock.lot.history'].sudo().create(history_vals)
    
    def action_cancel_reason_lot(self):        
        self._create_history_record(with_reason=True)
        self.lot_id.lot_status = 'cancelled' # Update the lot status to cancelled 
        # Post a message in the chatter for tracking
        message = f"Lot cancelled. Reason: {self.reason_id.name if self.reason_id else 'No reason provided'}"
        self.lot_id.message_post(body=message)

        return True
    def action_cancel(self):
        
        self._create_history_record()
        self.lot_id.lot_status = 'cancelled' # Update the lot status to cancelled 
        # Post a message in the chatter for tracking
        message = f"Lot cancelled. Reason: {self.reason_id.name if self.reason_id else 'No reason provided'}"
        self.lot_id.message_post(body=message)

        return True
