from odoo import models, fields, api
from datetime import datetime

class StockLotCancelWizard(models.TransientModel):
    _name = 'stock.lot.cancel.wizard'
    _description = 'Stock Lot Cancel Wizard'

    reason_id = fields.Many2one('stock.lot.cancel.reason', string='Reason')  # Reason is optional
    note = fields.Text(string='Note')  # Note is optional
    lot_id = fields.Many2one('stock.lot', string='Stock Lot', required=True)

    def action_cancel_lot(self):
        self.lot_id.with_context(is_from_cancellation_wizard=True).write({
            'cancel_reason_id': self.reason_id.id,
            'cancel_note': self.note,
        })

        # Post the cancellation in the chatter
        message = f"Lot cancelled. Reason: {self.reason_id.name if self.reason_id else 'No reason provided'}"
        self.lot_id.message_post(body=message)

        # Set context to prevent history creation in write
        

        return True
