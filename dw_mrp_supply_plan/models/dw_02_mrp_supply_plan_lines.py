from dateutil.relativedelta import relativedelta
from odoo import fields, api, models, _

from .utils import _domain_supply_products


class DwMrpSupplyPlanLines(models.Model):
    _name = "dw.mrp.supply.plan.lines"

    _description = ("MRP Yearly Product Supply plan lines (For each Product, each month's quantities are referenced, "
                    "fetched: displayed from dw.mrp.product.supply.plan) ")

    _sql_constraints = [
        ('unique_product_id_supply_plan_id', 'unique(product_id, supply_plan_id)',
         'Product must be unique within the same Supply Plan !')
    ]

    name = fields.Char('Ref', copy=False, default=_('New'))

    sequence = fields.Integer()

    # quantity = fields.Float(compute='_compute_monthly_supply_plans_total_quantity')

    quantity_planned = fields.Float(string="Planned Quantity", default=0.0,
                                    compute=lambda self: self._compute_monthly_supply_plans_total_quantity(
                                        'quantity_planned'))

    quantity_approved = fields.Float(string="Confirmed Quantity", default=0.0,
                                     compute=lambda self: self._compute_monthly_supply_plans_total_quantity(
                                         'quantity_approved'))

    quantity_done = fields.Float(string="Ordered Quantity", default=0.0,
                                 compute=lambda self: self._compute_monthly_supply_plans_total_quantity(
                                     'quantity_done'))

    quantity_to_order = fields.Float(string="Quantities to Order", default=0.0,
                                     compute=lambda self: self._compute_monthly_supply_plans_total_quantity(
                                         'quantity_to_order'))

    supply_plan_id = fields.Many2one('dw.mrp.supply.plan', ondelete='cascade')

    product_id = fields.Many2one('product.product', required=True,
                                 domain=lambda self: _domain_supply_products())

    uom_id = fields.Many2one('uom.uom', related='product_id.product_tmpl_id.uom_id')

    monthly_supply_plan_ids = fields.One2many('dw.mrp.product.supply.plan', 'product_supply_plan_id')

    # safety_stock_target = fields.Integer("Safety Stock Target")

    # lot_size = fields.Float(
    #     compute='_compute_lot_size',
    #     store=True
    # )

    company_id = fields.Many2one('res.company', related="supply_plan_id.company_id",
                                 default=lambda self: self.env.company, store=True)

    partner_id = fields.Many2one('res.partner', string='Supplier',
                                 change_default=True,
                                 tracking=True,
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 help="You can find a vendor by its Name, TIN, Email or Internal Reference.")

    #
    # def get_monthly_supply_plans(self):
    #     datas = []
    #     current_year = int(self.supply_plan_id.get_season_year())
    #     for month in range(1, 13):
    #         _date = date(current_year, month, 1)
    #         datas.append(
    #             (0, 0, {
    #                 'date': _date,
    #                 'date_launch': _date,
    #                 'product_supply_plan_id': self.id,
    #                 'product_id': self.product_id.id,
    #                 # 'start_quantity': self.product_id.product_tmpl_id.qty_available if month == 1 else 0
    #             })
    #         )
    #
    #     return datas

    def get_monthly_supply_plans(self):
        datas = []
        start_date = self.supply_plan_id.start_date
        end_date = self.supply_plan_id.end_date

        # Ensure start_date and end_date are valid
        if not start_date or not end_date or start_date > end_date:
            return datas  # Return an empty list if dates are invalid

        current_date = start_date

        while current_date <= end_date:
            datas.append(
                (0, 0, {
                    'date': current_date,
                    'date_launch': current_date,
                    'product_supply_plan_id': self.id,
                    'product_id': self.product_id.id,
                    # 'start_quantity': self.product_id.product_tmpl_id.qty_available if current_date.month == 1 else 0
                })
            )
            # Move to the first day of the next month
            current_date += relativedelta(months=1)

        return datas

    @api.depends('monthly_supply_plan_ids.quantity')
    def _compute_monthly_supply_plans_total_quantity(self, field_name):
        for record in self:
            # TODO: Which quantity to SUM
            record[field_name] = sum(record.monthly_supply_plan_ids.mapped(field_name))

    def action_view_product_monthly_supply_plan(self):
        tree_view = self.env.ref('dw_mrp_supply_plan.view_dw_mrp_product_monthly_supply_plan_tree')

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

        company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
        self_comp = self.with_company(company_id)

        # Check for supply_plan_id in vals
        supply_plan_id = vals.get('supply_plan_id')
        if supply_plan_id:
            supply_plan = self_comp.env['dw.mrp.supply.plan'].browse(supply_plan_id)
            if supply_plan.exists():
                product = self_comp.env['product.product'].browse(vals.get('product_id'))
                if product.exists():
                    internal_reference = product.default_code  # Assuming 'default_code' is the internal reference
                    vals['name'] = f"{supply_plan.name}-{internal_reference}"

        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'create_date' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals.get('create_date')))

            vals['name'] = self_comp.env['ir.sequence'].next_by_code('dw.mrp.supply.plan.lines',
                                                                     sequence_date=seq_date) or '/'

        result = super(DwMrpSupplyPlanLines, self_comp).create(vals)

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
