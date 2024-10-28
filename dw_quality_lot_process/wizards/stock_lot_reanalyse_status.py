from odoo import models, fields, api,Command, _
import datetime
from odoo.exceptions import UserError, ValidationError


class StockLotReanalyseLineWizard(models.TransientModel):
    _name = 'stock.lot.reanalyse.line.wizard'
    _description = 'Stock Lot reanalyse line Wizard'
    location_id = fields.Many2one(
        'stock.location', string='Location', domain=[('perform_quality_lot_reanalyze', '=', True)], check_company=True
    )
    quantity = fields.Float(string="Qte", default=1)
    uom_id = fields.Many2one(
        'uom.uom',
    )
    company_id = fields.Many2one(
        'res.company',readonly=0
    )


class StockLotReanalyseWizard(models.TransientModel):
    _name = 'stock.lot.reanalyse.wizard'
    _description = 'Stock Lot reanalyse Wizard'

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        lot_id = self.env['stock.lot'].browse(res["lot_id"])
        company_id =res["company_id"]
        quant_ids = lot_id.quant_ids.filtered(  lambda l: l.location_id.usage in ['internal'] and l.location_id.perform_quality_lot_reanalyze and l.quantity)
        line_ids = [
            Command.create({
                'location_id': quant.location_id.id,
                'company_id': company_id,
                'uom_id': quant.product_uom_id.id
            })
            for quant in quant_ids
        ]
        res["line_ids"] = line_ids
        return res

    company_id = fields.Many2one('res.company')

    reason_id = fields.Many2one('stock.lot.cancel.reason', string='Reason')
    note = fields.Text(string='Note')
    lot_id = fields.Many2one('stock.lot', string='Stock Lot', required=True)
    line_ids = fields.Many2many(
        'stock.lot.reanalyse.line.wizard', string='lines'
    )

