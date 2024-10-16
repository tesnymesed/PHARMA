from odoo import fields, models, api


class StockLocation(models.Model):
    _inherit = 'stock.location'

    must_check_lot_compiliance = fields.Boolean(string="Check Lot Confirmity", default=False,
                                      help='This field indicates if we should check lot confirmity in the location')
    @api.model
    def _default_lot_status(self):
        lot_status_conform = self.env.ref('dw_quality_lot_process.lot_status_conform')
        return [(6, 0, [lot_status_conform.id])]

    lot_status_for_tranfer_ids = fields.Many2many('lot.status', string='Lot status',
                                        default = lambda self : self._default_lot_status(),
                                        help="This field indicates the authorized lot status to transfer out/in the current location")
    
class LotStatus(models.Model):
    _name = 'lot.status'
    _description = 'Lot status'

    name = fields.Selection([
        ('quarantine', 'Quarantine'),
        ('conform', 'Conform'),
        ('not_conform', 'Not Conform'),
        ('blocked', 'Blocked'),
        ('cancelled', 'Cancelled')
    ], string="Lot Status")