from odoo import fields, models,api


class StockLocation(models.Model):
    _inherit = 'stock.location'

    
    perform_transfer = fields.Boolean(string ="Perform Transfer", default=True,help='This field indicates if we can perfom a tranfer from this location')
    @api.onchange('storage_category_id')
    
    def onchange_field(self):
        self.perform_transfer = self.storage_category_id.perform_transfer
    