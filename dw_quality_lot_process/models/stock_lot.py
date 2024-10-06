from odoo import api, fields, models


class StockLot(models.Model):
    _inherit = 'stock.lot'

    lot_status = fields.Selection([
        ('quarantine', 'Quarantine'),
        ('coform', 'Conform'),
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
    
    

    def action_set_conform(self):
        self.lot_status = 'coform'

    def action_set_not_conform(self):
        self.lot_status = 'not_conform'

    def action_set_blocked(self):
        self.lot_status = 'blocked'

    def action_set_cancelled(self):

        self.lot_status = 'cancelled'


    def action_set_in_progress(self):
        self.lot_status = 'in_progress'

    def action_set_analyzed(self):
        self.lot_status = 'analyzed'

    def action_set_reanalyzed(self):
        self.lot_status = 'reanalyzed'
