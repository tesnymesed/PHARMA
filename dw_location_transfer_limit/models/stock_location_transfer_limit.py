from odoo import fields, api, models, _


class StockLocationTransferLimit(models.Model):
    _name = 'stock.location.transfer.limit'
    _description = 'Stock Location Transfer Limit'

    name = fields.Char(string='Name', required=True)
    perform_transfer = fields.Boolean(string='Perform Transfer', default=True)
