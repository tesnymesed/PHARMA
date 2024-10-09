from odoo import models, fields, api

class StockLotCancelWizard(models.TransientModel):
    _name = 'stock.lot.cancel.wizard'
    _description = 'Stock Lot Cancel Wizard'

    reason_id = fields.Many2one('stock.lot.cancel.reason', string='Reason')  # Reason is optional
    note = fields.Text(string='Note')  # Note is optional
    lot_id = fields.Many2one('stock.lot', string='Stock Lot', required=True)
    

    def action_cancel_reason_lot(self):
        # Update lot status and cancellation reason
        history_vals = {}
        history_vals.update({
            'lot_id': self.lot_id.id,
            'user_id': self.env.user.id,
            'change_date': fields.Datetime.now(),
            'previous_status': self.lot_id.lot_status,
            'new_status': 'cancelled',
            'reason_id': self.reason_id.id,
            'note' : self.note
        })
        self.env['stock.lot.history'].sudo().create(history_vals)

        self.lot_id.lot_status = 'cancelled'
        # Post a message in the chatter for tracking
        message = f"Lot cancelled. Reason: {self.reason_id.name if self.reason_id else 'No reason provided'}"
        self.lot_id.message_post(body=message)

        return True
    def action_cancel(self):
        history_vals = {}
        history_vals.update({
            'lot_id': self.lot_id.id,
            'user_id': self.env.user.id,
            'change_date': fields.Datetime.now(),
            'previous_status': self.lot_id.lot_status,
            'new_status': 'cancelled',
        })
        self.env['stock.lot.history'].sudo().create(history_vals)

        self.lot_id.lot_status = 'cancelled'
        # Post a message in the chatter for tracking
        message = f"Lot cancelled. Reason: {self.reason_id.name if self.reason_id else 'No reason provided'}"
        self.lot_id.message_post(body=message)

        return True
