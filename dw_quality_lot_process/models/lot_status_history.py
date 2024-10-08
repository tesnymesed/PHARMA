from odoo import models, fields, api
from datetime import datetime

class LotStatusHistory(models.Model):
    _name = 'stock.lot.history'
    _description = 'Lot Status History'

    lot_id = fields.Many2one('stock.lot', string="Lot", required=True, ondelete='cascade')

    previous_status = fields.Selection([
        ('quarantine', 'Quarantine'),
        ('conform', 'Conform'),
        ('not_conform', 'Not Conform'),
        ('blocked', 'Blocked'),
        ('cancelled', 'Cancelled')
    ], string="Previous Status", required=True)
    
    new_status = fields.Selection([
        ('quarantine', 'Quarantine'),
        ('conform', 'Conform'),
        ('not_conform', 'Not Conform'),
        ('blocked', 'Blocked'),
        ('cancelled', 'Cancelled')
    ], string="New Status", required=True)

    change_date = fields.Datetime(string="Change Date", default=lambda self: fields.Datetime.now())

    user_id = fields.Many2one('res.users', string="Changed By", default=lambda self: self.env.user)

