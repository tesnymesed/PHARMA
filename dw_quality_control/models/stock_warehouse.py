from odoo import fields, models


class DwStockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    dw_quality_operation_id = fields.Many2one('stock.picking.type', string="Type d'opération de Qualité")
