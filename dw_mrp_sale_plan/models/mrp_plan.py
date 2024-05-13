from odoo import fields, api, models, _

from dateutil.relativedelta import relativedelta
import math


class DwMrpPlanLines(models.Model):
    _inherit = "mrp.plan.lines"
    sale_plan_id = fields.Many2one(
        'sale.plan', related="plan_id.sale_plan_id", store=1
    )


class DwProductMrpPlan(models.Model):
    _inherit = "product.mrp.plan"
    sale_plan_id = fields.Many2one(
        'sale.plan', related="product_plan_id.sale_plan_id", store=1
    )

    sale_planned_quantity = fields.Float(
        compute='_compute_sale_planned_quantity'
    )
    real_sale_quantity = fields.Float(
        compute='_compute_sale_planned_quantity',
        help='The last 6 months from this date'
    )
    sale_capacity = fields.Float(
        compute='_compute_sales_capacity'
    )
    autonomy = fields.Float(
        compute='_compute_autonomy'
    )
    expected_final_quantity = fields.Float(
        compute='_compute_expected_final_quantities',
    )

    @api.depends('expected_start_quantity', 'quantity', 'sale_planned_quantity', 'sale_capacity')
    def _compute_autonomy(self):
        for record in self:
            if record.expected_start_quantity + record.quantity - record.sale_planned_quantity > 0:
                record.autonomy = (
                                          record.expected_start_quantity + record.quantity - record.sale_planned_quantity
                                  ) / max(record.sale_planned_quantity, 1)
            else:
                record.autonomy = record.sale_capacity

    @api.depends('expected_start_quantity', 'quantity', 'sale_planned_quantity')
    def _compute_sales_capacity(self):
        for record in self:
            if (record.expected_start_quantity + record.quantity) > record.sale_planned_quantity:
                record.sale_capacity = record.sale_planned_quantity
            else:
                record.sale_capacity = record.expected_start_quantity + record.quantity

    @api.depends('product_id', 'date')
    def _compute_sale_planned_quantity(self):
        sale_plan = self.env['product.sale.plan.monthly']
        real_sales = self.env['sale.order.line']

        for record in self:
            real_sale_planned = real_sales.search([
                ('product_id', '=', record.product_id.id),
                ('order_id.date_order', '>=', record.date + relativedelta(months=-6)),
            ])
            record.real_sale_quantity = sum(real_sale_planned.mapped('qty_delivered'))

            sale_plan_domain = [
                ('id', 'in',
                 record.product_plan_id.plan_id.sale_plan_id.product_plan_ids.mapped('monthly_plan_ids').ids),
                ('date', '=', record.date),
            ]

            if record.product_plan_id.plan_id.sale_plan_id:
                sale_plan_search = sale_plan.search(sale_plan_domain)
            else:
                sale_plan_search = sale_plan.search([
                    ('product_plan_id.product_id', '=', record.product_id.id),
                    ('date', '=', record.date),
                ])

            record.sale_planned_quantity = sum(sale_plan_search.mapped("quantity"))

            if record.quantity == 0 and not record.no_manufacturing:
                if record.sale_planned_quantity < record.lot_size:
                    record.quantity = record.lot_size
                elif record.sale_planned_quantity != 0:
                    if record.sale_planned_quantity % record.lot_size == 0:
                        record.quantity = record.sale_planned_quantity
                    else:
                        rate = math.ceil(record.sale_planned_quantity / record.lot_size)
                        record.quantity = rate * record.lot_size

    @api.depends('quantity')
    def _compute_expected_final_quantities(self):
        for record in self:
            record.expected_final_quantity = record.unexpected_quantity + record.expected_start_quantity + record.quantity - \
                                             record.sale_planned_quantity


class DwMrpPlan(models.Model):
    _inherit = 'mrp.plan'

    sale_plan_id = fields.Many2one(
        'sale.plan',
        domain="['|',('company_id', '=', company_id),('company_id', '=', False)]",

    )

    @api.onchange('sale_plan_id')
    def _update_lines_by_bom_id(self):
        if self.sale_plan_id:
            lines = [
                (0, 0, {
                    'product_id': line.product_id.id,
                    # 'sale_plan_id': self.sale_plan_id.id,
                    'bom_id': line.product_id.bom_ids and line.product_id.bom_ids[0].id or False,
                }) for line in self.sale_plan_id.product_plan_ids if line.product_id.bom_ids
            ]

            deleteable = self.product_plan_ids.filtered(
                lambda o: o.sale_plan_id and o.sale_plan_id.id != self.sale_plan_id.id and not any(
                    o.monthly_plan_ids.mapped('roadmap_done'))
            ).ids

            self.product_plan_ids = [(2, l) for l in deleteable] + lines
        else:
            deleteable = self.product_plan_ids.filtered(
                lambda o: o.sale_plan_id and not any(o.monthly_plan_ids.mapped('roadmap_done'))
            ).ids

            self.product_plan_ids = [(2, l) for l in deleteable]
