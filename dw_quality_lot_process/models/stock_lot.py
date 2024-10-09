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
        history_vals = {}
        history_vals.update({
            'lot_id': self.id,
            'user_id': self.env.user.id,
            'change_date': fields.Datetime.now(),
            'previous_status': self.lot_status,
            'new_status': 'quarantine',
        })
        self.env['stock.lot.history'].sudo().create(history_vals)
        self.lot_status = 'quarantine'

    def action_set_conform(self):
        history_vals = {}
        history_vals.update({
            'lot_id': self.id,
            'user_id': self.env.user.id,
            'change_date': fields.Datetime.now(),
            'previous_status': self.lot_status,
            'new_status': 'conform',
        })
        self.env['stock.lot.history'].sudo().create(history_vals)
        self.lot_status = 'conform'

    def action_set_not_conform(self):
        history_vals = {}
        history_vals.update({
            'lot_id': self.id,
            'user_id': self.env.user.id,
            'change_date': fields.Datetime.now(),
            'previous_status': self.lot_status,
            'new_status': 'not_conform',
        })
        self.env['stock.lot.history'].sudo().create(history_vals)
        self.lot_status = 'not_conform'

    def action_set_blocked(self):
        history_vals = {}
        history_vals.update({
            'lot_id': self.id,
            'user_id': self.env.user.id,
            'change_date': fields.Datetime.now(),
            'previous_status': self.lot_status,
            'new_status': 'blocked',
        })
        self.env['stock.lot.history'].sudo().create(history_vals)
        self.lot_status = 'blocked'

    def action_set_cancelled(self):
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
        history_vals = {}
        history_vals.update({
            'lot_id': self.id,
            'user_id': self.env.user.id,
            'change_date': fields.Datetime.now(),
            'previous_lot_quarantine_status': self.lot_quarantine_status,
            'new_lot_quarantine_status': 'in_progress',
        })
        self.env['stock.lot.history'].sudo().create(history_vals)

        self.lot_quarantine_status = 'in_progress'

    def action_set_analyzed(self):
        history_vals = {}
        history_vals.update({
            'lot_id': self.id,
            'user_id': self.env.user.id,
            'change_date': fields.Datetime.now(),
            'previous_lot_quarantine_status': self.lot_quarantine_status,
            'new_lot_quarantine_status': 'analyzed',
        })
        self.env['stock.lot.history'].sudo().create(history_vals)

        self.lot_quarantine_status = 'analyzed'

    def action_set_reanalyzed(self):
        history_vals = {}
        history_vals.update({
            'lot_id': self.id,
            'user_id': self.env.user.id,
            'change_date': fields.Datetime.now(),
            'previous_lot_quarantine_status': self.lot_quarantine_status,
            'new_lot_quarantine_status': 'reanalyzed',
        })
        self.env['stock.lot.history'].sudo().create(history_vals)
        self.lot_quarantine_status = 'reanalyzed'