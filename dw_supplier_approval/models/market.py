# -*- coding:utf-8 -*-

from odoo import fields, models,api,_



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
        store=True,

        group_expand='_expand_states'
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
    domain=['|','|',('homologue', '=', True), ('categ_id.homologue', '=', True), ('product_tmpl_id.homologue', '=', True),('purchase_ok','=',True)],

    )
    market_type_id = fields.Many2one('dw.market.type', string="Market type")
    purchase_ids = fields.Many2many("purchase.order", string="Purchase Order")
    homologation_ids = fields.Many2many("dw.homologation", 'market_id', string="Homologation")

    supplier_homologuer_ids = fields.Many2many(
        'res.partner',
        compute="_compute_supplier_homologuer"
    )
    cahier_charge_attachment = fields.Binary(string="Specification document")
    cahier_charge_name = fields.Char(string='File name')
    def _expand_states(self, states, domain, order):
        return [key for key, dummy in self._fields['state'].selection]
    def button_draft(self):
        self.write({"state": "draft"})

    @api.depends('homologation_ids')
    def _compute_supplier_homologuer(self):
        for record in self :
            search = record.homologation_ids.search([('state', '=', 'homologue'),('market_id','=',record.id)])
            supplier_ids = search.mapped('supplier_id')
            record.supplier_homologuer_ids = supplier_ids

    def action_homologation(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'Market Document',
            'res_model': 'dw.document.market.wizard',
            'views': [[self.env.ref('dw_supplier_approval.view_document_market_wizard').id, 'form']],
            'target': 'new',

            'context': {
                'default_market_id': self.id
            }
        }
        self.write({"state": "homologation_cosultation"})

    def action_done(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Market Document',
            'res_model': 'dw.document.market.wizard',
            'views': [[self.env.ref('dw_supplier_approval.view_document_market_wizard').id, 'form']],
            'target': 'new',

            'context': {
                'default_market_id': self.id
            }
        }

    def show_documents(self):
        self.ensure_one()
        return {
            'res_model': 'documents.document',
            'type': 'ir.actions.act_window',
            'name': _("%(market_name)s 's Documents", market_name=self.name),

            'domain': [
                ('res_model', '=', 'dw.market'), ('res_id', '=', self.id),
            ],
            'view_mode': 'kanban,tree,form',

            'context': {'default_res_model': 'dw.market', 'default_res_id': self.id,
                        'searchpanel_default_folder_id': self.env.ref("dw_supplier_approval.folder_dw_market").id,
                        'limit_folders_to_lead': True},
        }

    def action_cancel(self):
        self.write({"state": "cancel"})
