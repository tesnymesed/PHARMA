from odoo import api, fields, models


class StockLot(models.Model):
    _inherit = 'stock.lot'

    lot_status = fields.Selection([
        ('quarantine', 'Quarantine'),
        ('conform', 'Conform'),
        ('not_conform', 'Not Conform'),
        ('blocked', 'Blocked'),
        ('cancelled', 'Cancelled')
    ], string="Lot status", default='quarantine')

    lot_quarantine_status = fields.Selection([
        ('draft','Draft'),
        ('in_progress', 'In progress'),
        ('analyzed','Analyzed'),
        ('reanalyzed','reanalyzed')
        ],string="Lot status", default='draft')
    
    compiliance_check = fields.Boolean(related='product_id.requires_lot_compliance_check',readonly=True)
    lot_status_history_ids = fields.One2many('stock.lot.history', 'lot_id', string="Status History")
    cancel_reason_id = fields.Many2one(
        'stock.lot.cancel.reason', 
        string='Cancel Reason'
    )
    cancel_note = fields.Text(string="Cancellation Note")


    def action_set_quarantine(self):
        self.lot_status = 'quarantine'

    def action_set_conform(self):
        self.lot_status = 'conform'

    def action_set_not_conform(self):
        self.lot_status = 'not_conform'

    def action_set_blocked(self):
        self.lot_status = 'blocked'

    def action_set_cancelled(self):
        self.lot_status = 'cancelled'
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cancel Lot',
            'res_model': 'stock.lot.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_lot_id': self.id}
        }

    # quarantine status
    def action_set_in_progress(self):
        self.lot_quarantine_status = 'in_progress'

    def action_set_analyzed(self):
        self.lot_quarantine_status = 'analyzed'

    def action_set_reanalyzed(self):
        self.lot_quarantine_status = 'reanalyzed'
    
    # in case modification in lot_status or lot_quarantine_status create records in stock.lot.history for the current lot
    def write(self, vals):
        for record in self:
            # Skip history creation if the change is coming from the cancellation wizard
            if self.env.context.get('is_from_cancellation_wizard', False):
                return super(StockLot, self).write(vals)

            history_vals = {
                'lot_id': record.id,
                'user_id': self.env.user.id,
                'change_date': fields.Datetime.now(),
            }

            # Track status change
            if 'lot_status' in vals:
                history_vals.update({
                    'previous_status': record.lot_status,
                    'new_status': vals.get('lot_status'),
                })

            # Track quarantine status change
            if 'lot_quarantine_status' in vals:
                history_vals.update({
                    'previous_lot_quarantine_status': record.lot_quarantine_status,
                    'new_lot_quarantine_status': vals.get('lot_quarantine_status'),
                })

            # If it's a cancellation, include the reason and note if available
            if 'lot_status' in vals and vals.get('lot_status') == 'cancelled':
                history_vals.update({
                    'reason_id': vals.get('cancel_reason_id'),  # Reason from the wizard (if any)
                    'note': vals.get('cancel_note'),  # Note from the wizard (if any)
                })

            # Create the history record
            self.env['stock.lot.history'].sudo().create(history_vals)

        return super(StockLot, self).write(vals)
