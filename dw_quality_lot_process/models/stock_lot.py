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

    # quarantine status
    def action_set_in_progress(self):
        self.lot_quarantine_status = 'in_progress'

    def action_set_analyzed(self):
        self.lot_quarantine_status = 'analyzed'

    def action_set_reanalyzed(self):
        self.lot_quarantine_status = 'reanalyzed'
    
    # in case modification in lot_status create records in stock.lot.history for the current lot
    def write(self, vals):
        if 'lot_status' in vals:
            for record in self:
                self.env['stock.lot.history'].create({
                    'lot_id': record.id,
                    'previous_status': record.lot_status,
                    'new_status': vals.get('lot_status'),
                    'user_id': self.env.user.id,
                })
        return super(StockLot, self).write(vals)
