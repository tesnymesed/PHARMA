from odoo import fields, models, api


class StockLocation(models.Model):
    _inherit = 'stock.location'

    @api.model
    def _default_lot_status(self):
        lot_status_conform = self.env.ref('dw_quality_lot_process.stock_lot_status_conform')
        return [(6, 0, [lot_status_conform.id])]

    lot_status_for_transfer_ids = fields.Many2many('stock.lot.status', string='Lot status',
                                                   default=lambda self: self._default_lot_status(),
                                                   help="This field indicates the authorized lot status to transfer out/in the current location")

    must_check_lot_compliance = fields.Boolean(string="Check Lot Conformity", default=False,
                                                help='This field indicates if we should check lot conformity in the location')


class StockLotStatus(models.Model):
    _name = 'stock.lot.status'
    _description = 'Lot status'

    name = fields.Selection([
        ('quarantine', 'Quarantine'),
        ('conform', 'Conform'),
        ('not_conform', 'Not Conform'),
        ('blocked', 'Blocked'),
        ('cancelled', 'Cancelled')
    ], string="Lot Status", required=True)
