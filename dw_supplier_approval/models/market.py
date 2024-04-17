# -*- coding:utf-8 -*-

from odoo import fields, models,api


class DwMarket(models.Model):
    _name = 'dw.market'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Supplier Approval"
    name = fields.Char(string="Name", required=True)
    state = fields.Selection(
        selection= [
            ('draft', 'Draft'),
            ('progress', 'In Progress'),
            ('done', 'Done'),
            ('cancel','Cancel')
        ],
        string="State",
        default="draft",
    )

    description = fields.Text(string="Description")
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
    )
    user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user)
    product_id = fields.Many2one(
        'product.product',
        check_company=True,
    domain=['|',('homologue', '=', True), ('categ_id.homologue', '=', True)],
    )
    market_type_id = fields.Many2one('dw.market.type',string="Market type")
    purchase_ids = fields.Many2many("purchase.order",string="Purchase Order")
    homologation_ids = fields.Many2many("dw.homologation",'market_id',string="Homologation")

    supplier_homologuer_ids = fields.Many2many(
        'res.partner',
        compute="_compute_supplier_homologuer"
    )


    # def _compute_production_ids(self):
    #     for rec in self:
    #         workorder_ids = self.get_user_workorder(rec.user_id, False)
    #         # Get all productions related to the pending workorders
    #         production_ids = workorder_ids.mapped('production_id').filtered(
    #             lambda production: production.company_id.id == self.company_id.id)
    #         rec.production_ids = production_ids
    @api.depends('homologation_ids')
    def _compute_supplier_homologuer(self):
        supliers_ids =[]
        for rec in self :
            search = self.env['dw.homologation'].search([('market_id','=',self.id),('state','=','homologue')])
            supplier_ids = search.mapped('supplier_id')
            rec.supplier_homologuer_ids = supplier_ids
    def action_done(self):
        self.write({"state": "done"})

    def action_progress(self):
            self.write({"state": "progress"})

    def action_cancel(self):
        self.write({"state": "cancel"})




