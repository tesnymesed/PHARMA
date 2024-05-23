from datetime import date

from odoo import fields, api, models, _

from .utils import _domain_supply_products


class DwMrpSupplyPlanLines(models.Model):
    _name = "dw.mrp.supply.plan.lines"

    _description = "MRP Yearly Product Supply plan lines (For each Product, each month's quantities are referenced, fetched: displayed from dw.mrp.product.supply.plan) "

    _sql_constraints = [
        ('unique_product_id_supply_plan_id', 'unique(product_id, supply_plan_id)',
         'Product must be unique within the same Supply Plan !')
    ]

    supply_plan_id = fields.Many2one('dw.mrp.supply.plan', ondelete='cascade')

    product_id = fields.Many2one('product.product', required=True,
                                 domain=lambda self: _domain_supply_products())

    # quantity = fields.Float(compute='_compute_monthly_supply_plans_total_quantity')

    quantity_planned = fields.Float(string="Planned Quantity", default=0.0,
                                    compute=lambda self: self._compute_monthly_supply_plans_total_quantity('quantity_planned'))

    quantity_approved = fields.Float(string="Confirmed Quantity", default=0.0,
                                     compute=lambda self: self._compute_monthly_supply_plans_total_quantity('quantity_approved'))

    quantity_done = fields.Float(string="Ordered Quantity", default=0.0,
                                 compute=lambda self: self._compute_monthly_supply_plans_total_quantity('quantity_done'))

    quantity_to_order = fields.Float(string="Quantities to Order", default=0.0,
                                     compute=lambda self: self._compute_monthly_supply_plans_total_quantity('quantity_to_order'))

    sequence = fields.Integer()

    uom_id = fields.Many2one('uom.uom', related='product_id.product_tmpl_id.uom_id')

    monthly_supply_plan_ids = fields.One2many('dw.mrp.product.supply.plan', 'product_supply_plan_id')

    # safety_stock_target = fields.Integer("Safety Stock Target")

    # lot_size = fields.Float(
    #     compute='_compute_lot_size',
    #     store=True
    # )

    company_id = fields.Many2one('res.company', related="supply_plan_id.company_id", store=True)

    partner_id = fields.Many2one('res.partner', string='Supplier',
                                 change_default=True,
                                 tracking=True,
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 help="You can find a vendor by its Name, TIN, Email or Internal Reference.")

    def get_monthly_supply_plans(self):
        datas = []
        current_year = int(self.supply_plan_id.get_season_year())
        for month in range(1, 13):
            _date = date(current_year, month, 1)
            datas.append(
                (0, 0, {
                    'date': _date,
                    'date_launch': _date,
                    'product_supply_plan_id': self.id,
                    'product_id': self.product_id.id,
                    # 'start_quantity': self.product_id.product_tmpl_id.qty_available if month == 1 else 0
                })
            )

        return datas

    @api.depends('monthly_supply_plan_ids.quantity')
    def _compute_monthly_supply_plans_total_quantity(self, field_name):
        for record in self:
            # TODO: Which quantity to SUM
            record[field_name] = sum(record.monthly_supply_plan_ids.mapped(field_name))

    def action_view_product_monthly_supply_plan(self):
        tree_view = self.env.ref('dw_mrp_supply_plan.view_dw_mrp_product_monthly_supply_plan_form')

        return {
            'name': _("Product's Monthly Supply Plan"),
            'type': 'ir.actions.act_window',
            'res_model': 'dw.mrp.product.supply.plan',
            'views': [(tree_view.id, 'tree')],
            'view_mode': 'tree',
            'context': {
                'default_product_supply_plan_id': self.id,
                'default_product_id': self.product_id.id,
            },
            'domain': [('product_supply_plan_id', '=', self.id)],
            'target': 'new',
        }

    # @api.onchange('product_id')
    # def _onchange_product_id(self):
    #     if self.product_id:
    #         bom_ids = self.product_id.product_tmpl_id.bom_ids
    #         if bom_ids:
    #             self.bom_id = bom_ids[0]
    #         else:
    #             self.bom_id = False

    @api.model
    def create(self, vals):
        result = super().create(vals)
        for res in result:
            res.monthly_supply_plan_ids = res.get_monthly_supply_plans()
        return result

    # @api.depends('bom_id')
    # def _compute_lot_size(self):
    #     for record in self:
    #         record.lot_size = record.bom_id.product_qty

    def get_roadmaps_per_lines(self):
        datas = []
        for record in self:
            datas.extend(
                record.monthly_supply_plan_ids.filtered(lambda l: l if l.roadmap_id else None).mapped('roadmap_id').ids)
        return datas

    def print_plan_summary_report(self):
        return self.env.ref('dw_mrp_supply_plan.action_mrp_monthly_supply_plan_report').report_action(self)
