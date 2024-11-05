from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _


class DwMrpProductTarget(models.Model):
    _name = 'dw.mrp.product.target'
    _description = "Product's Production Targets"

    name = fields.Char('Ref', copy=False, required=True, default=_('New'))

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', readonly=True)

    production_objective_qty = fields.Float(string="Production Objective Qty", default=0.0,
                                            compute=lambda self: self._compute_product_monthly_target_total_quantity(
                                                'production_objective_qty')
                                            )
    sales_objective_qty = fields.Float(string="Sales Objective Qty", default=0.0,
                                       compute=lambda self: self._compute_product_monthly_target_total_quantity(
                                           'sales_objective_qty'))

    target_id = fields.Many2one('dw.mrp.production.target', ondelete='cascade', string="Target")

    company_id = fields.Many2one('res.company', related="target_id.company_id",
                                 default=lambda self: self.env.company, store=True)

    product_id = fields.Many2one('product.product', required=True, domain=[
        # ('product_tmpl_id.type', '=', 'product'),
        # ('product_tmpl_id.categ_id.is_final_product', '=', True),
        # ('product_tmpl_id.bom_ids', '!=', False),
        '|',
        ('product_tmpl_id.company_id', '=', company_id),
        ('product_tmpl_id.company_id', '=', False)
    ])
    uom_id = fields.Many2one('uom.uom', related='product_id.product_tmpl_id.uom_id')

    company_id = fields.Many2one('res.company', related="target_id.company_id",
                                 default=lambda self: self.env.company, store=True)

    product_monthly_target_ids = fields.One2many('dw.mrp.product.monthly.target', 'product_target_id')

    def get_product_monthly_target_lines(self):
        datas = []

        start_date = self.target_id.start_date
        end_date = self.target_id.end_date

        # Ensure start_date and end_date are valid
        if not start_date or not end_date or start_date > end_date:
            return datas  # Return an empty list if dates are invalid

        current_date = start_date

        while current_date <= end_date:
            datas.append(
                (0, 0, {
                    'date': current_date,
                    'product_target_id': self.id,
                    'product_id': self.product_id.id,
                })
            )
            # Move to the first day of the next month
            current_date += relativedelta(months=1)

        return datas

    def action_view_product_monthly_targets(self):
        tree_view = self.env.ref('dw_mrp_production_target.view_dw_mrp_product_monthly_targets_tree')

        return {
            'name': _("Product's Monthly Production Targets"),
            'type': 'ir.actions.act_window',
            'res_model': 'dw.mrp.product.monthly.target',
            'views': [(tree_view.id, 'tree')],
            'view_mode': 'tree',
            'context': {
                'default_product_target_id': self.id,
                'default_product_id': self.product_id.id,
            },
            'domain': [('product_target_id', '=', self.id)],
            'target': 'new',
        }

    @api.depends('product_monthly_target_ids')
    def _compute_product_monthly_target_total_quantity(self, field_name):
        for record in self:
            # TODO: Which quantity to SUM
            record[field_name] = sum(record.product_monthly_target_ids.mapped(field_name))

    def action_approve(self):
        self.state = 'approved'

    def action_done(self):
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancelled'

    @api.model
    def create(self, vals):

        company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
        self_comp = self.with_company(company_id)

        # Check for target_id in vals
        target_id = vals.get('target_id')
        if target_id:
            target_id_i = self_comp.env['dw.mrp.production.target'].browse(target_id)
            if target_id_i.exists():
                product = self_comp.env['product.product'].browse(vals.get('product_id'))
                if product.exists():
                    internal_reference = product.default_code  # Assuming 'default_code' is the internal reference
                    vals['name'] = f"{target_id_i.name}-{internal_reference}"

        # if vals.get('name', _('New')) == _('New'):
        #     seq_date = None
        #     if 'create_date' in vals:
        #         seq_date = fields.Datetime.context_timestamp(self,
        #                                                      fields.Datetime.to_datetime(vals.get('create_date')))
        #
        #     vals['name'] = self_comp.env['ir.sequence'].next_by_code('dw.mrp.product.target',
        #                                                              sequence_date=seq_date) or '/'

        result = super(DwMrpProductTarget, self_comp).create(vals)

        for res in result:
            res.product_monthly_target_ids = res.get_product_monthly_target_lines()

        return result
