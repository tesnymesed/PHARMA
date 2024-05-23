from odoo import fields, models, _


class DwMrpSupplyPlan(models.Model):
    _name = 'dw.mrp.supply.plan'
    _description = 'MRP Yearly Supply plan'

    _sql_constraints = [
        ('unique_season_date_company', 'unique(season_date, company_id)',
         'Season Date must be unique within the same company!')
    ]

    name = fields.Char(required=True)

    season_date = fields.Char(required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        # ('confirmed', 'Confirmed'),
        ('approved', 'Approved'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', readonly=True)

    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)

    product_supply_plan_ids = fields.One2many('dw.mrp.supply.plan.lines', 'supply_plan_id')

    def get_season_year(self):
        return self.season_date

    def action_mrp_product_supply_plan(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'name': _('Product Supply Plan'),
            'tag': 'mrp_product_supply_plan',
            'context': {'res_id': self.id}
        }

    def get_year_months(self):
        _year = self.create_date.strftime('%y')
        return [
            'Jan-' + _year,
            'Fev-' + _year,
            'Mar-' + _year,
            'Apr-' + _year,
            'May-' + _year,
            'Jun-' + _year,
            'Jul-' + _year,
            'Aug-' + _year,
            'Sep-' + _year,
            'Oct-' + _year,
            'Nov-' + _year,
            'Dec-' + _year,
        ]

    def run_action(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'owl.main_dashboard'
        }

    # def action_print(self):
    #     return self.env.ref('dw_mrp_supply_plan.action_mrp_plan_report').report_action(self)

    #
    # def action_confirm(self):
    #     self.state = 'confirmed'

    def action_approve(self):
        self.state = 'approved'
        self.product_supply_plan_ids.monthly_supply_plan_ids.action_approve()

    def action_done(self):
        self.state = 'done'
        # TODO: Check
        self.product_supply_plan_ids.monthly_supply_plan_ids.action_done()
    # def action_draft(self):
    #     self.state = 'draft'
    #     # TODO: Check
    #     self.product_supply_plan_ids.monthly_supply_plan_ids.action_done()

    def action_cancel(self):
        self.state = 'cancelled'

    def unlink(self):
        for record in self:
            for plan in record.product_supply_plan_ids:
                plan.monthly_supply_plan_ids.unlink()
                plan.unlink()
        return super().unlink()

    def action_display_all_roadmaps(self):
        datas = self.product_supply_plan_ids.get_roadmaps_per_lines()
        action = self.env["ir.actions.actions"]._for_xml_id("dw_mrp_supply_plan.mrp_roadmap_action")
        action['domain'] = [('id', '=', datas)]
        return action

    def action_import_excel_view(self):
        form_view = self.env.ref('dw_mrp_supply_plan.view_mrp_plan_import_excel_form')
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
