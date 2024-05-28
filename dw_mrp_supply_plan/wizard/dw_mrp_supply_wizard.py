# -*- coding: utf-8 -*-
from odoo import api, fields, models

from collections import defaultdict


class DwMrpSupplyWizard(models.TransientModel):
    _name = 'dw.mrp.supply.wizard'
    _description = 'MRP Supply Tool: Create Purchase Orders From Product Supply Plan entries '

    company_id = fields.Many2one('res.company', string='Company', required=True)
    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)

    product_supply_plan_ids = fields.Many2many('dw.mrp.product.supply.plan', string='Products to Supply')

    @api.model
    def default_get(self, fields):
        res = super(DwMrpSupplyWizard, self).default_get(fields)
        res['company_id'] = self.env.company.id
        return res

    def action_fetch_supply_plan(self):
        self.ensure_one()
        supply_plan_records = self.env['dw.mrp.product.supply.plan'].search([
            ('company_id', '=', self.company_id.id),
            ('date_launch', '>=', self.date_from),
            ('date_launch', '<=', self.date_to)
        ])
        self.product_supply_plan_ids = supply_plan_records
        return {
            'type': 'ir.actions.act_window',
            'name': 'MRP Supply Plan',
            'res_model': 'dw.mrp.supply.wizard',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
        }

    def action_create_rfqs(self):
        self.ensure_one()
        # Group the product supply records by supplier and create RFQs
        grouped_by_supplier = self.product_supply_ids.groupby('supplier_id')
        for supplier, records in grouped_by_supplier:
            # Create an RFQ for the current supplier
            rfq = self.env['purchase.order'].create({
                'partner_id': supplier.id,
                'order_line': [(0, 0, {
                    'product_id': rec.product_id.id,
                    'product_qty': rec.quantity,
                    'price_unit': rec.unit_price,
                    'date_planned': rec.date_launch,
                }) for rec in records]
            })
        return True


class MrpProductionSplitLine(models.TransientModel):
    _name = 'dw.production.split.line'
    _description = "Split Production Detail"

    mrp_production_split_id = fields.Many2one(
        'mrp.production.split', 'Split Production', required=True, ondelete="cascade")
    quantity = fields.Float('Quantity To Produce', digits='Product Unit of Measure', required=True)
    user_id = fields.Many2one(
        'res.users', 'Responsible',
        domain=lambda self: [('groups_id', 'in', self.env.ref('mrp.group_mrp_user').id)])
    date = fields.Datetime('Schedule Date')
