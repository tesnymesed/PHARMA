from odoo import fields, models

from .utils import _domain_supply_products


class DwMrpProductSupplyPlan(models.Model):
    _name = 'dw.mrp.product.supply.plan'
    _description = "Product's MONTHLY supply plan. For one Product, for EACH month, quantities are set stored"
    _order = 'date asc'

    date = fields.Date()

    date_launch = fields.Date()

    state = fields.Selection([('proposed', 'Proposed'), ('approved', 'Approved'), ('done', 'Done')], default='proposed')

    quantity_planned = fields.Float(string="Planned Quantity", default=0.0)

    quantity_approved = fields.Float(string="Confirmed Quantity", default=0.0)

    quantity_done = fields.Float(string="Ordered Quantity", default=0.0)

    quantity_to_order = fields.Float(string="Quantities to Order", default=0.0)

    # Parent
    product_supply_plan_id = fields.Many2one('dw.mrp.supply.plan.lines', ondelete='cascade')

    company_id = fields.Many2one('res.company', related="product_supply_plan_id.company_id", store=1)

    product_id = fields.Many2one('product.product', required=True,
                                 domain=lambda self: _domain_supply_products())

    uom_id = fields.Many2one('uom.uom', related='product_id.product_tmpl_id.uom_id')

    partner_id = fields.Many2one('res.partner', string='Supplier',
                                 change_default=True,
                                 tracking=True,
                                 related="product_supply_plan_id.partner_id",
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
        self.state = 'approved'
        self.write({
            'state': 'approved',
            'quantity_approved': self.quantity_planned,
            'quantity_to_order': self.quantity_planned,
        })

    def action_done(self):
        self.write({'state': 'done', 'quantity_done': self.quantity_to_order})
