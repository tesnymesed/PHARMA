# -*- coding:utf-8 -*-

from odoo import fields, models, api


class DwMarket(models.Model):
    _name = 'dw.market'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Supplier Approval"
    name = fields.Char(string="Name", required=True)
    state = fields.Selection(
        selection=[
            ('draft', 'Identification of the need'),
            ('homologation_cosultation', 'Approval/consultation'),
            ('done', 'Assigned'),
            ('cancel', 'Canceled')
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
    product_ids = fields.Many2many(
        'product.product',
        check_company=True,
        domain=['|', '|', ('homologue', '=', True), ('categ_id.homologue', '=', True),
                ('product_tmpl_id.homologue', '=', True)],
    )
    market_type_id = fields.Many2one('dw.market.type', string="Market type")
    purchase_ids = fields.Many2many("purchase.order", string="Purchase Order")
    homologation_ids = fields.Many2many("dw.homologation", 'market_id', string="Homologation")

    supplier_homologuer_ids = fields.Many2many(
        'res.partner',
        compute="_compute_supplier_homologuer"
    )

    def button_draft(self):
        self.write({"state": "draft"})

    @api.depends('homologation_ids')
    def _compute_supplier_homologuer(self):
        for record in self :
            search = record.homologation_ids.search([('state', '=', 'homologue'),('market_id','=',record.id)])
            supplier_ids = search.mapped('supplier_id')
            record.supplier_homologuer_ids = supplier_ids

    def action_homologation(self):
        self.write({"state": "homologation_cosultation"})

    def action_done(self):
        self.write({"state": "done"})

    def action_cancel(self):
        self.write({"state": "cancel"})
