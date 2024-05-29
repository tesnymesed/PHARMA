# -*- coding: utf-8 -*-
from collections import defaultdict

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _


class DwMrpSupplyWizard(models.Model):
    _name = 'dw.mrp.supply.wizard'
    _description = 'MRP Supply Tool: Create Purchase Orders From Product Supply Plan entries '

    name = fields.Char('Reference', copy=False, default=_('New'))

    company_id = fields.Many2one('res.company', string='Company')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')

    product_supply_plan_ids = fields.Many2many('dw.mrp.product.supply.plan', string='Products to Supply')

    purchase_order_preview_ids = fields.One2many('dw.purchase.order.preview', 'wizard_id',
                                                 string='Purchase Order Preview')

    grouping_options = fields.Many2many('dw.mrp.supply.wizard.grouping.option', string='Grouping Options')

    @api.model
    def default_get(self, field_list):
        res = super(DwMrpSupplyWizard, self).default_get(field_list)
        res['company_id'] = self.env.company.id
        res['date_from'] = fields.Date.today()
        res['date_to'] = fields.Date.today() + relativedelta(months=3)

        return res

    def action_fetch_supply_plan(self):
        self.ensure_one()
        _domain = [('state', '=', 'approved')]

        if self.company_id:
            _domain.append(('company_id', '=', self.company_id.id))

        if self.date_from:
            _domain.append(('date_launch', '>=', self.date_from))

        if self.date_to:
            _domain.append(('date_launch', '<=', self.date_to))

        self.product_supply_plan_ids = self.env['dw.mrp.product.supply.plan'].search(_domain)

        return {
            'type': 'ir.actions.act_window',
            'name': 'MRP Supply Wizard',
            'res_model': 'dw.mrp.supply.wizard',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
        }

    def action_create_purchase_orders(self):
        self.ensure_one()
        # Group the product supply records based on the selected grouping options

        # Group the records by 'company_id', 'date_launch'
        # grouped_records = groupby(self.product_supply_plan_ids, key=lambda r: (r.company_id))
        # # Process the grouped data
        # result = []
        # for (company, date_launch), group in grouped_records:
        #     group_records = list(group)
        #     # Perform operations on the group, such as calculating the sum or count
        #     total_quantity = sum(r.quantity_to_order for r in group_records)
        #     result.append({
        #         'company_id': company.id,
        #         # 'partner': self.partner_id,
        #         'total_quantity': total_quantity
        #     })
        #
        # result = []
        # for product_id, product_lines in grouped_records:
        #     total_quantity = sum(line.quantity_to_order for line in product_lines)
        #     result.append({'product_id': product_id, 'quantity_to_order': total_quantity})
        #
        # # _grouped = self.env['dw.mrp.product.supply.plan'].read_group(
        # #     domain=_domain,
        # #     fields=['company_id',
        # #             'partner_id',
        # #             'quantity_planned', 'quantity_approved', 'quantity_to_order',
        # #             'product_supply_plan_id',
        # #             'supply_plan_id',
        # #             'product_id', 'uom_id',
        # #             ],
        # #     groupby=['company_id'],
        # # )
        #
        grouped_records = defaultdict(list)
        for record in self.product_supply_plan_ids:
            key = [record.company_id, record.date_launch]
            for option in self.grouping_options:
                if option.name == 'partner':
                    key.append(record.partner_id)
                # elif option.name == 'incoterm':
                #     key.append(record.incoterm_id)
            # key.append(record.product_id)

            grouped_records[tuple(key)].append(record)

        self.purchase_order_preview_ids = self.env['dw.purchase.order.preview']

        for key, records in grouped_records.items():
            _prx = {
                'company_id': next((k for k in key if k._name == 'res.company'), self.company_id).id,
                'date_planned': key[1],
            }

            if 'partner' in [o.name for o in self.grouping_options]:
                # _prx['partner_id'] = next((k for k in key if k._name == 'res.partner'), False).id
                _prx['partner_id'] = key[2].id

            if 'incoterm' in [o.name for o in self.grouping_options]:
                _prx['incoterm_id'] = next((k for k in key if k._name == 'account.incoterms'), False).id

            order_line_vals = [(0, 0, {
                'product_id': rec.product_id.id,
                'product_qty': rec.quantity_to_order,
                # 'price_unit': rec.unit_price,
                'date_planned': rec.date_launch,
            }) for rec in records]

            _prx['order_line_ids'] = order_line_vals

            purchase_order_preview = self.env['dw.purchase.order.preview'].create(_prx)

            self.purchase_order_preview_ids += purchase_order_preview

        return {
            'type': 'ir.actions.act_window',
            'name': 'MRP Supply Wizard',
            'res_model': 'dw.mrp.supply.wizard',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
        }


class PurchaseOrderPreview(models.Model):
    _name = 'dw.purchase.order.preview'
    _description = 'Purchase Order Preview'

    name = fields.Char('Ref', copy=False, default=_('New'))

    wizard_id = fields.Many2one('dw.mrp.supply.wizard', string='Wizard')
    partner_id = fields.Many2one('res.partner', string='Supplier')
    company_id = fields.Many2one('res.company', string='Company')
    # incoterm_id = fields.Many2one('account.incoterms', string='Incoterm')
    date_planned = fields.Date(string='Planned Date')

    order_line_ids = fields.One2many('dw.purchase.order.preview.line', 'preview_id', string='Order Lines')


class PurchaseOrderPreviewLine(models.Model):
    _name = 'dw.purchase.order.preview.line'
    _description = 'Purchase Order Preview Line'

    name = fields.Char('Ref', copy=False, default=_('New'))

    preview_id = fields.Many2one('dw.purchase.order.preview', string='Preview')
    product_id = fields.Many2one('product.product', string='Product')
    product_qty = fields.Float(string='Quantity')
    price_unit = fields.Float(string='Unit Price')
    date_planned = fields.Date(string='Planned Date')
