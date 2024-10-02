from odoo import fields, models


class StockLocation(models.Model):
    _inherit = 'stock.location'

    
    perform_transfer = fields.Boolean(string ="Perform Transfer", default=True)