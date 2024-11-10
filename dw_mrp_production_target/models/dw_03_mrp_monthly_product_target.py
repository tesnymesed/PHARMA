from odoo import models, fields, api, _


class DwMrpProductMonthlyTarget(models.Model):
    _name = 'dw.mrp.product.monthly.target'
    _description = "Product's MONTHLY production targets. For one Product, for EACH month, quantities are set stored"
    _order = 'date asc'

    name = fields.Char('Ref', copy=False, default=_('New'))

    date = fields.Date()

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string="Status", default='draft', readonly=True)

    production_objective_qty = fields.Float(string="Production Objective Qty", default=19000.0)
    sales_objective_qty = fields.Float(string="Sales Objective Qty", default=19000.0)

    company_id = fields.Many2one('res.company', related="product_target_id.company_id",
                                 default=lambda self: self.env.company, store=True)

    product_id = fields.Many2one('product.product', required=True,
                                 related="product_target_id.product_id",
                                 store=True,
                                 # domain=[('product_tmpl_id.categ_id.is_final_product', '=', True),
                                 #         '|',
                                 #         ('product_tmpl_id.company_id', '=', company_id),
                                 #         ('product_tmpl_id.company_id', '=', False)
                                 #         ],
                                 # domain=lambda self: _domain_pf_products()
                                 # domain="[('product_tmpl_id.categ_id.is_final_product', '=', True),('product_tmpl_id.company_id', '=', company_id)]"
                                 )

    uom_id = fields.Many2one('uom.uom', related='product_id.product_tmpl_id.uom_id')

    # Parent
    product_target_id = fields.Many2one('dw.mrp.product.target', ondelete='cascade')

    target_id = fields.Many2one('dw.mrp.production.target', ondelete='cascade',
                                related='product_target_id.target_id', store=True)

    def action_approve(self):
        # for record in self:
        self.write({
            'state': 'approved',
        })

    def action_reject(self):
        # for record in self:
        self.write({
                'state': 'rejected',
            })

    def action_done(self):
        # for record in self:
        self.write({'state': 'done'})

    def action_cancel(self):
        # for record in self:
        self.write({'state': 'cancelled'})

    @api.model
    def create(self, vals):
        company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
        self_comp = self.with_company(company_id)

        # Check for product_target_id in vals
        product_target_id = vals.get('product_target_id')
        if product_target_id:
            product_target_id = self_comp.env['dw.mrp.product.target'].browse(product_target_id)
            if product_target_id.exists():
                date_ref = vals.get('date').strftime('%m%y')
                vals['name'] = f"{product_target_id.name}-{date_ref}"

        # if vals.get('name', _('New')) == _('New'):
        #     seq_date = None
        #     if 'create_date' in vals:
        #         seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals.get('create_date')))
        #
        #     _name = self_comp.env['ir.sequence'].next_by_code('dw.mrp.product.monthly.target',
        #                                                       sequence_date=seq_date) or '/'
        #     _parts = _name.split('P-M-Bench/')
        #     if _parts:
        #         _parts[0] = _parts[0].rstrip('/')
        #         month_name = format_date(self.env, vals.get('date'), date_format='MMM yyyy')
        #         _parts.insert(1, month_name)
        #         _parts.insert(1, 'MB')  # Adjust prefix as needed
        #         _name = '/'.join(_parts)
        #
        #     vals['name'] = _name

        result = super(DwMrpProductMonthlyTarget, self_comp).create(vals)

        return result
