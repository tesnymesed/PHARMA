from odoo import fields, models


class StockLocation(models.Model):
    _inherit = 'stock.location'

    location_transfer_limit_id = fields.Many2one(
        'stock.location.transfer.limit',
        string='Location Transfer Limit',
        help='This field indicates if we can perfom a tranfer from this location'
        
        )