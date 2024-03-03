import calendar
import datetime

from dateutil.relativedelta import relativedelta

from odoo import fields, api, models, _
from odoo.exceptions import UserError

cnt = 10
list1 = []
for i in range(datetime.datetime.today().year - 2, datetime.datetime.today().year + 5):
    list1.append((str(cnt), str(i)))
    cnt = cnt + 1


class SalePlan(models.Model):
    _name = 'sale.plan'

    name = fields.Char()
    season_date = fields.Selection(
        selection=list1,
        required=True
    )
    product_plan_ids = fields.One2many(
        'product.sale.plan',
        'plan_id'
    )
    plan_id = fields.Many2one(
        'sale.plan'
    )
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)

    def get_the_year(self):
        return dict(self._fields['season_date'].selection).get(self.season_date)

    def action_compare_plan(self):
        if not self.plan_id:
            raise UserError(_("Please select a plan to compare with"))

        plan_dict = {line.product_id: (line.name, line.quantity) for line in self.plan_id.product_plan_ids}

        for product_plan in self.product_plan_ids:
            product_id = product_plan.product_id
            if product_id in plan_dict:
                compared_name, compared_quantity = plan_dict[product_id]
                product_plan.write({
                    'compared_product_id': product_id,
                    'compared_name': compared_name,
                    'compared_quantity': compared_quantity,
                })

    def get_month_year(self):
        month_year_list = []

        for i in range(12):
            current_month = (self.create_date + relativedelta(months=i)).strftime('%b-%y')
            month_year_list.append(current_month)

        return month_year_list

    def action_print(self):
        return self.env.ref('dw_sale_plan.action_sale_plan_report').report_action(self)

    @api.model
    def create(self, values):
        if not values.get('name'):
            sequence_id = int(self.env['ir.config_parameter'].sudo().get_param('dw_sale_plan_sequence_id'))
            sequence = self.env['ir.sequence'].browse(sequence_id)
            values['name'] = sequence.next_by_id() if sequence else "New"
        return super(SalePlan, self).create(values)


class ProductSalePlan(models.Model):
    _name = 'product.sale.plan'

    name = fields.Char()
    product_id = fields.Many2one(
        'product.product',
        # domain=[('product_tmpl_id.categ_id.is_final_product', '=', True)],
    )
    quantity = fields.Float(
        compute='_compute_monthly_plan_ids',
    )
    uom_id = fields.Many2one(
        'uom.uom',
        related='product_id.product_tmpl_id.uom_id'
    )
    plan_id = fields.Many2one(
        'sale.plan',
        ondelete='cascade'
    )
    company_id = fields.Many2one('res.company', related="plan_id.company_id", store=True)
    sequence = fields.Integer()
    compared_product_id = fields.Many2one(
        'product.product',
        store=True,
        readonly=1
    )
    compared_quantity = fields.Float(
        store=True,
        readonly=1
    )
    compared_name = fields.Char(
        store=True,
        readonly=1
    )
    monthly_plan_ids = fields.One2many(
        'product.sale.plan.monthly',
        'product_plan_id',
    )

    def get_months(self):
        datas = []
        year = self.plan_id.get_the_year()
        for month in range(1, 13):
            datas.append((0, 0, {
                'date': datetime.date.today().replace(month=month, day=1, year=int(year)),
                'product_plan_id': self.id
            }))

        return datas

    @api.depends('monthly_plan_ids.quantity')
    def _compute_monthly_plan_ids(self):
        for record in self:
            record.quantity = sum(record.monthly_plan_ids.mapped('quantity'))

    def action_view_quantity_by_month(self):
        tree_view = self.env.ref('dw_sale_plan.view_sale_plan_months_form')

        return {
            'name': _('Monthly Plan'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.sale.plan.monthly',
            'views': [(tree_view.id, 'tree')],
            'view_mode': 'tree',
            'context': {'default_product_plan_id': self.id},
            'domain': [('product_plan_id', '=', self.id)],
            'target': 'new',
        }

    def create(self, vals):
        result = super().create(vals)
        for res in result:
            res.monthly_plan_ids = res.get_months()
        return result


class ProductSalePlanMonthly(models.Model):
    _name = 'product.sale.plan.monthly'

    quantity = fields.Float()
    date = fields.Date()
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    product_plan_id = fields.Many2one(
        'product.sale.plan',
        ondelete='cascade'
    )
    last_sold_quantity = fields.Float(
        compute='_compute_last_sold_quantities'
    )

    @api.depends('product_plan_id.product_id')
    def _compute_last_sold_quantities(self):
        SaleOrderLine = self.env['sale.order.line']
        for record in self:
            record.last_sold_quantity = sum(
                SaleOrderLine.search([('product_id', '=', record.product_plan_id.product_id.id),
                                      ('company_id', '=', record.product_plan_id.company_id.id),
                                      ('order_id.date_order', '>=', record.date + relativedelta(years=-1)),
                                      ('order_id.date_order', '<=', record.date.replace(
                                          day=calendar.monthrange(record.date.year, record.date.month)[
                                              1]) + relativedelta(years=-1)),
                                      ('order_id.state', 'in', ('done', 'sale'))]).mapped('qty_delivered'))
