import datetime
from dateutil.relativedelta import relativedelta
from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from datetime import date, timedelta

cnt = 10
list1 = []
for i in range(2010, datetime.datetime.today().year + 5):
    list1.append((str(cnt), str(i)))
    cnt = cnt + 1


class MrpPlan(models.Model):
    _name = 'mrp.plan'

    name = fields.Char(
        required=True
    )
    season_date = fields.Selection(
        selection=list1,
        required=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ],
        default='draft'
    )
    product_plan_ids = fields.One2many(
        'mrp.plan.lines',
        'plan_id',
    )

    excel_file = fields.Binary()
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)

    def get_the_year(self):
        return dict(self._fields['season_date'].selection).get(self.season_date)

    def action_product_mrp_plan(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'name': _('Product Mrp Plan'),
            'tag': 'mrp_plan',
            'context': {'res_id': self.id}
        }

    def get_month_year(self):
        return [
            'Jan-' + self.create_date.strftime('%y'),
            'Fev-' + self.create_date.strftime('%y'),
            'Mar-' + self.create_date.strftime('%y'),
            'Apr-' + self.create_date.strftime('%y'),
            'May-' + self.create_date.strftime('%y'),
            'Jun-' + self.create_date.strftime('%y'),
            'Jul-' + self.create_date.strftime('%y'),
            'Aug-' + self.create_date.strftime('%y'),
            'Sep-' + self.create_date.strftime('%y'),
            'Oct-' + self.create_date.strftime('%y'),
            'Nov-' + self.create_date.strftime('%y'),
            'Dec-' + self.create_date.strftime('%y'),
        ]

    def action_print(self):
        return self.env.ref('dw_mrp_plan.action_mrp_plan_report').report_action(self)

    def action_done(self):
        self.state = 'done'
        self.product_plan_ids.monthly_plan_ids.action_done()

    def action_cancel(self):
        self.state = 'cancel'

    def unlink(self):
        for record in self:
            for plan in record.product_plan_ids:
                plan.monthly_plan_ids.unlink()
                plan.unlink()
        return super().unlink()

    def action_display_all_roadmaps(self):
        datas = self.product_plan_ids.get_roadmaps_per_lines()
        action = self.env["ir.actions.actions"]._for_xml_id("dw_mrp_plan.mrp_roadmap_action")
        action['domain'] = [('id', '=', datas)]
        return action

    def action_import_excel_view(self):
        form_view = self.env.ref('dw_mrp_plan.view_mrp_plan_import_excel_form')
        action = {
            'name': _('Excel'),
            'type': 'ir.actions.act_window',
            'res_model': self._name,
        }

        action['views'] = [(form_view.id, 'form')]
        action['view_mode'] = 'form'
        action['res_id'] = self.id

        action['target'] = 'new'

        return action


class MrpPlanLines(models.Model):
    _name = "mrp.plan.lines"
    product_id = fields.Many2one(
        'product.product',
        required=True,
        domain=[('product_tmpl_id.categ_id.is_final_product', '=', True), ('product_tmpl_id.bom_ids', '!=', False)],
    )
    bom_id = fields.Many2one(
        'mrp.bom',
        'BoM',
        store=True,
    )
    quantity = fields.Float(
        compute='_compute_monthly_plan_ids',
    )
    uom_id = fields.Many2one(
        'uom.uom',
        related='product_id.product_tmpl_id.uom_id'
    )
    monthly_plan_ids = fields.One2many(
        'product.mrp.plan',
        'product_plan_id',
    )
    plan_id = fields.Many2one(
        'mrp.plan',
        ondelete='cascade'
    )
    sequence = fields.Integer()
    lot_size = fields.Float(
        compute='_compute_lot_size',
        store=True
    )

    company_id = fields.Many2one('res.company', related="plan_id.company_id", store=True)

    def get_months(self):
        datas = []
        current_year = int(self.plan_id.get_the_year())
        for month in range(1, 13):
            start_date = date(current_year, month, 1)
            datas.append(
                (0, 0, {
                    'date': start_date,
                    'product_plan_id': self.id,
                    'product_id': self.product_id.id,
                    'start_quantity': self.product_id.product_tmpl_id.qty_available if month == 1 else 0
                })
            )

        return datas

    @api.depends('monthly_plan_ids.quantity')
    def _compute_monthly_plan_ids(self):
        for record in self:
            record.quantity = sum(record.monthly_plan_ids.mapped('quantity'))

    def action_view_quantity_by_month(self):
        tree_view = self.env.ref('dw_mrp_plan.view_mrp_plan_months_form')

        return {
            'name': _('Monthly Plan'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.mrp.plan',
            'views': [(tree_view.id, 'tree')],
            'view_mode': 'tree',
            'context': {
                'default_product_plan_id': self.id,
                'default_product_id': self.product_id.id,
            },
            'domain': [('product_plan_id', '=', self.id)],
            'target': 'new',
        }

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            bom_ids = self.product_id.product_tmpl_id.bom_ids
            if bom_ids:
                self.bom_id = bom_ids[0]
            else:
                self.bom_id = False

    def create(self, vals):
        result = super().create(vals)
        for res in result:
            mrp_plan_interval_type = self.env['ir.config_parameter'].sudo().get_param('mrp.mrp_plan_interval')
            if mrp_plan_interval_type == "weekly":
                res.monthly_plan_ids = res.get_weeks()

            else:
                res.monthly_plan_ids = res.get_months()
        return result

    @api.depends('bom_id')
    def _compute_lot_size(self):
        for record in self:
            record.lot_size = record.bom_id.product_qty

    @api.depends('monthly_plan_ids.quantity')
    def _compute_monthly_plan_ids(self):
        for record in self:
            record.quantity = sum(record.monthly_plan_ids.mapped('quantity'))

    def get_roadmaps_per_lines(self):
        datas = []
        for record in self:
            datas.extend(
                record.monthly_plan_ids.filtered(lambda l: l if l.roadmap_id else None).mapped('roadmap_id').ids)
        return datas

    def print_plan_summary_report(self):
        return self.env.ref('dw_mrp_plan.action_mrp_plan_monthly_report').report_action(self)

class ProductMrpPlan(models.Model):
    _name = 'product.mrp.plan'
    _order = 'date asc'

    product_plan_weekly_ids = fields.One2many(
            'product.mrp.plan.weekly',
            'mrp_plan_monthly_id',
    )

    product_id = fields.Many2one(
        'product.product',
        domain=[('product_tmpl_id.categ_id.is_final_product', '=', True), ('product_tmpl_id.bom_ids', '!=', False)],
        required=True
    )
    quantity = fields.Float()
    uom_id = fields.Many2one(
        'uom.uom',
        related='product_id.product_tmpl_id.uom_id'
    )
    date = fields.Date()
    product_plan_id = fields.Many2one(
        'mrp.plan.lines',
        ondelete='cascade'
    )
    qty_available = fields.Float(
        'Quantity On Hand',
        compute='_compute_product_internal_values'
    )
    bom_quantity = fields.Float()
    virtual_available = fields.Float(
        'Forecast Quantity',
        compute='_compute_product_internal_values'
    )
    free_qty = fields.Float(
        'Free To Use Quantity',
        compute='_compute_product_internal_values'
    )
    lot_size = fields.Float(
        related='product_plan_id.lot_size',
    )
    mrp_state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
    ],
        default='draft'
    )
    quantity_estimation = fields.Char(
        'Free to Use / On Hand',
        compute='_compute_quantity_estimation'
    )
    total_planned_quantity = fields.Float()

    monthly_planned_quantity = fields.Float()
    roadmap_id = fields.Many2one(
        'mrp.roadmap'
    )
    start_quantity = fields.Float()
    expected_start_quantity = fields.Float(
        compute='compute_expected_start_quantity',
    )
    expected_final_quantity = fields.Float(
        compute='_compute_expected_final_quantities',
    )
    unexpected_quantity = fields.Float()
    no_manufacturing = fields.Boolean(
        default=False
    )
    mip_quantity = fields.Float()

    roadmap_done = fields.Boolean(
        compute="_compute_roadmap_done"
    )
    company_id = fields.Many2one('res.company', related="product_plan_id.company_id", store=1)

    @api.depends('roadmap_id')
    def _compute_roadmap_done(self):
        for record in self:
            if record.roadmap_id:
                record.roadmap_done = True
            else:
                record.roadmap_done = False


    @api.onchange('no_manufacturing')
    def _onchange_no_manufacturing(self):
        self.quantity = 0

    def action_done(self):
        self.mrp_state = 'done'

    @api.constrains('quantity', 'product_id')
    def _check_quantity(self):
        for record in self:
            if record.lot_size > 0:
                if record.quantity % record.lot_size > 0:
                    raise ValidationError(_("You cannot set a quantity that doesn't multiply the lot size"))



    @api.depends('quantity')
    def _compute_expected_final_quantities(self):
        for record in self:
            record.expected_final_quantity = record.unexpected_quantity + record.expected_start_quantity + record.quantity
            # - record.sale_planned_quantity

    @api.depends('quantity', 'expected_start_quantity')
    def compute_expected_start_quantity(self):
        for record in self:
            # expected quantities
            if record.date.month == 1:
                record.expected_start_quantity = record.start_quantity
            else:
                record.expected_start_quantity = self.search([
                    ('date', '=', record.date + relativedelta(months=-1)),
                    ('product_id', '=', record.product_id.id)]).mapped('expected_final_quantity')[0]

    def _prepare_datas_to_roadmap(self):
        datas = {
            'product_id': self.product_id.id,
            'company_id': self.company_id.id,
            'date': self.date,
            'mrp_line_plan_id': self.id,
            'quantity': self.quantity,
            'bom_id': self.product_plan_id.bom_id.id,
            'quantity_per_lot': self.product_plan_id.bom_id.product_qty
        }
        return datas

    def action_create_roadmap_wizard(self):
        datas = self._prepare_datas_to_roadmap()
        res = self.env['mrp.roadmap'].create(datas)

        form_view = self.env.ref('dw_mrp_plan.view_mrp_roadmap_form')
        action = {
            'name': _('Roadmap'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.roadmap',
        }

        action['views'] = [(form_view.id, 'form')]
        action['view_mode'] = 'form'
        action['target'] = 'current'
        action['res_id'] = res.id

        self.write({
            'roadmap_id': res.id
        })

        return action

    def create(self, vals):
        result = super(ProductMrpPlan, self).create(vals)
        class_name = self.__class__.__name__
        if class_name == 'product.mrp.plan':
            for res in result:
                weeks = res.get_weeks(res.date)
                weekly_objs = [self.env['product.mrp.plan.weekly'].create(week) for week in weeks]
                res.product_plan_weekly_ids = [(6, 0, [obj.id for obj in weekly_objs])]
        return result

    def get_weeks(self,date):
        dates = []
        week_dates = self.generate_week_dates(date)
        for index, week in enumerate(week_dates):
            dates.append(
                {
                    'date': week,
                    'mrp_plan_monthly_id': self.id,
                    'product_plan_id': self.product_plan_id.id,
                    'product_id': self.product_id.id,
                    'start_quantity': self.product_id.product_tmpl_id.qty_available if index == 0 else 0
                }
            )

        return dates
    def generate_week_dates(self,date):
        first_day_of_month = date
        days_to_first_sunday = (first_day_of_month.weekday() + 1)
        days_to_next_sunday = (7 - days_to_first_sunday) % 7
        first_week_start_date = first_day_of_month - datetime.timedelta(days=days_to_next_sunday)
        week_dates = [first_week_start_date + datetime.timedelta(weeks=week) for week in range(5)
                      if (first_week_start_date + datetime.timedelta(weeks=week)).month == date.month]
        return week_dates

    def action_view_quantity_by_week(self):
        tree_view = self.env.ref('dw_mrp_plan.view_mrp_plan_weekly_tree')
        return {
            'name': _('Weekly Plan'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.mrp.plan.weekly',
            'views': [(tree_view.id, 'tree')],
            'view_mode': 'tree',
            'context': {
                'default_product_plan_id': self.id,
                'default_product_id': self.product_id.id,
            },
            'domain': [('mrp_plan_monthly_id', '=', self.id)],
            'target': 'new',
        }

    @api.depends('free_qty', 'qty_available')
    def _compute_quantity_estimation(self):
        for record in self:
            record.quantity_estimation = str(round(record.free_qty, 2)) + " / " + str(round(record.qty_available, 2))

    @api.depends('product_plan_id.product_id')
    def _compute_product_internal_values(self):
        for record in self:
            record.qty_available = record.product_plan_id.product_id.product_tmpl_id.qty_available
            record.free_qty = record.product_plan_id.product_id.free_qty
            record.virtual_available = record.product_plan_id.product_id.product_tmpl_id.virtual_available

class ProductMrpPlanWeekly(models.Model):
    _name = 'product.mrp.plan.weekly'
    _description = 'Weekly Mrp Plan Product'
    _inherit = 'product.mrp.plan'
    _inherit_exclude = ['product_plan_weekly_ids']
    _order = 'date asc'

    mrp_plan_monthly_id = fields.Many2one(
            'product.mrp.plan'
    )

    test = fields.Float()

    def create(self, vals):
        return super(ProductMrpPlanWeekly, self).create(vals)

    def write(self, vals):
        result = super(ProductMrpPlanWeekly, self).write(vals)
        # update monthly Qty
        if 'quantity' in vals:
            month_qty = sum((self.env['product.mrp.plan.weekly']
                         .search([('mrp_plan_monthly_id.id', '=', self.mrp_plan_monthly_id.id)]))
                         .mapped('quantity'))
            self.mrp_plan_monthly_id.quantity = month_qty
        return result

    def compute_expected_start_quantity(self):
        for record in self:
            # expected quantities
            if record.date.day < 8:
                record.expected_start_quantity = record.start_quantity
            else:
                record.expected_start_quantity = self.search([
                    ('date', '=', record.date + relativedelta(weeks=-1)),
                    ('product_id', '=', record.product_id.id)]).mapped('expected_final_quantity')[0]

    def _prepare_datas_to_roadmap(self):
        datas = {
            'product_id': self.product_id.id,
            'company_id': self.company_id.id,
            'date': self.date,
            'mrp_line_weekly_plan_id': self.id,
            'quantity': self.quantity,
            'bom_id': self.product_plan_id.bom_id.id,
            'quantity_per_lot': self.product_plan_id.bom_id.product_qty
        }
        return datas