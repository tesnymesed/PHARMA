from odoo import api, fields, models, _
from odoo.tools.misc import format_date

from .utils import _domain_supply_products, _PFX_PRODUCT_SUPPLY_PLAN


class DwMrpProductSupplyPlan(models.Model):
    _name = 'dw.mrp.product.supply.plan'
    _description = "Product's MONTHLY supply plan. For one Product, for EACH month, quantities are set stored"
    _order = 'date asc'

    name = fields.Char('Ref', copy=False, default=_('New'))

    date = fields.Date()

    date_launch = fields.Date()

    state = fields.Selection([('proposed', 'Proposed'), ('approved', 'Approved'), ('done', 'Done')], default='proposed')

    quantity_planned = fields.Float(string="Planned Quantity", default=0.0)

    quantity_approved = fields.Float(string="Confirmed Quantity", default=0.0)

    quantity_done = fields.Float(string="Ordered Quantity", default=0.0)

    quantity_to_order = fields.Float(string="Quantities to Order", default=0.0)

    # Parent
    product_supply_plan_id = fields.Many2one('dw.mrp.supply.plan.lines', ondelete='cascade')

    supply_plan_id = fields.Many2one('dw.mrp.supply.plan', ondelete='cascade',
                                     related='product_supply_plan_id.supply_plan_id', store=1)

    company_id = fields.Many2one('res.company', related="product_supply_plan_id.company_id",
                                 default=lambda self: self.env.company, store=1)

    product_id = fields.Many2one('product.product', required=True,
                                 related="product_supply_plan_id.product_id",
                                 store=1,
                                 domain=lambda self: _domain_supply_products())

    uom_id = fields.Many2one('uom.uom', related='product_id.product_tmpl_id.uom_id')

    partner_id = fields.Many2one('res.partner', string='Supplier',
                                 change_default=True,
                                 tracking=True,
                                 related="product_supply_plan_id.partner_id",
                                 store=1,
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 help="You can find a vendor by its Name, TIN, Email or Internal Reference.")

    # roadmap_id = fields.Many2one('mrp.roadmap')

    # @api.depends('roadmap_id')
    # def _compute_roadmap_done(self):
    #     for record in self:
    #         if record.roadmap_id:
    #             record.roadmap_done = True
    #         else:
    #             record.roadmap_done = False

    def action_approve(self):
        self.write({
            'state': 'approved',
            'quantity_approved': self.quantity_planned,
            'quantity_to_order': self.quantity_planned,
        })

    def action_done(self):
        self.write({'state': 'done', 'quantity_done': self.quantity_to_order})

    @api.model
    def create(self, vals):

        company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
        self_comp = self.with_company(company_id)

        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'create_date' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals.get('create_date')))

            _name = self_comp.env['ir.sequence'].next_by_code('dw.mrp.product.supply.plan',
                                                              sequence_date=seq_date) or '/'
            _parts = _name.split('PSP/')
            if _parts:
                _parts[0] = _parts[0].rstrip('/')
                month_name = format_date(self.env, vals.get('date'), date_format='MMM yyyy')
                _parts.insert(1, month_name)
                _parts.insert(1, _PFX_PRODUCT_SUPPLY_PLAN)
                _name = '/'.join(_parts)

            vals['name'] = _name

        result = super(DwMrpProductSupplyPlan, self_comp).create(vals)

        return result
