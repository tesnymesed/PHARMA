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
    
    def _create_history_record(self, previous_status, new_status, is_quarantine=False):
        '''This function creates stock.lot.history record'''
        history_vals = {
            'lot_id': self.id,
            'user_id': self.env.user.id,
            'change_date': fields.Datetime.now(),
            'previous_status' if not is_quarantine else 'previous_lot_quarantine_status': previous_status,
            'new_status' if not is_quarantine else 'new_lot_quarantine_status': new_status,
        }
        self.env['stock.lot.history'].sudo().create(history_vals)
    
    #lot status buttons
    def action_set_quarantine(self):
        self._create_history_record(self.lot_status, 'quarantine')
        self.lot_status = 'quarantine'

    def action_set_conform(self):
        self._create_history_record(self.lot_status, 'conform')
        self.lot_status = 'conform'
    
    def action_set_not_conform(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cancel Lot',
            'res_model': 'stock.lot.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_lot_id': self.id,'default_status':'not_conform'}
        }

    def action_set_blocked(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cancel Lot',
            'res_model': 'stock.lot.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_lot_id': self.id,'default_status':'blocked'}
        }

    def action_set_cancelled(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cancel Lot',
            'res_model': 'stock.lot.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_lot_id': self.id,'default_status':'cancelled'}
        }
        

    # Analyse status buttons
    def action_set_in_progress(self):
        self._create_history_record(self.lot_quarantine_status, 'in_progress', is_quarantine=True)
        self.lot_quarantine_status = 'in_progress'


    def action_set_analyzed(self):
        self._create_history_record(self.lot_quarantine_status, 'analyzed', is_quarantine=True)
        self.lot_quarantine_status = 'analyzed'

    def action_set_reanalyzed(self):
        self._create_history_record(self.lot_quarantine_status, 'reanalyzed', is_quarantine=True)
        self.lot_quarantine_status = 'reanalyzed'