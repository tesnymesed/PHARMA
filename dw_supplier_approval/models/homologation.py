# -*- coding:utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class DwHomologation(models.Model):
    _name = 'dw.homologation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', default=lambda self: _('New'))

    state = fields.Selection(
        selection=[
            ('prospection', 'Prospection'),
            ('analyse', 'Analyse'),
            ('audit', 'Audit'),
            ('lot_validation', 'Lot Validation'),
            ('qualification', 'Qualification'),
            ('homologue', 'approved'),
            ('cancel', 'Canceled')
        ],
        string="State",
        default="prospection",
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
    )
    market_id = fields.Many2one('dw.market', string='Market', domain="[('state','=','homologation_cosultation')]")
    product_id = fields.Many2one(
        'product.product',
        check_company=True,
        compute="_compute_product", readonly=False, store=True, domain="[('id','in',product_ids)]"
    )
    lot_validation = fields.Boolean('Lot Validation')
    supplier_id = fields.Many2one(
        'res.partner',
        domain='[("is_supplier","=", True)]'
    )
    dw_supplier_nature = fields.Selection(
        [('fabricant', 'Fabricant'), ('regroupeur', 'Regroupeur')],
        string="Supplier nature", related="supplier_id.dw_supplier_nature",readonly=False,store=True,
    )
    product_ids = fields.Many2many(
        'product.product',
        related="market_id.product_ids"
    )
    email = fields.Char('Email')
    phone = fields.Char('Phone')
    # address fields
    street = fields.Char(string="Address")
    street2 = fields.Char()
    zip = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', )
    country_code = fields.Char(related='country_id.code', string="Country Code")
    purchase_id = fields.Many2one("purchase.order", string="Purchase Order")

    manufacturing_document_attachment = fields.Binary(string="Document fabriquant")
    manufacturing_file_name = fields.Char(string='File name')

    rapport_expertise_attachment = fields.Binary(string="Document d\'expertise")
    rapport_expertise_file_name = fields.Char(string='File name')

    rapport_audit_attachment = fields.Binary(string="Document d\'audit")
    rapport_audit_file_name = fields.Char(string='File name')

    fichier_stabilite_attachment = fields.Binary(string="Fichier de stabilité")
    fichier_stabilite_file_name = fields.Char(string='File name')

    @api.depends('market_id')
    def _compute_product(self):
        for rec in self:
            if rec.market_id:
                rec.product_id = rec.market_id.product_ids[0]
            else:
                rec.product_id = False

    @api.onchange("supplier_id")
    def onchange_address(self):
        self.street = self.supplier_id.street if self.supplier_id else False
        self.street2 = self.supplier_id.street2 if self.supplier_id else False
        self.zip = self.supplier_id.zip if self.supplier_id else False
        self.city = self.supplier_id.city if self.supplier_id else False
        self.country_id = self.supplier_id.country_id if self.supplier_id else False
        self.state_id = self.supplier_id.state_id if self.supplier_id else False
        self.phone = self.supplier_id.phone if self.supplier_id else False
        self.email = self.supplier_id.email if self.supplier_id else False

    def action_to_analyse(self):

        if self.dw_supplier_nature == 'regroupeur':
            return {
                'type': 'ir.actions.act_window',
                'name': 'Manufacturing Document',
                'res_model': 'dw.document.wizard',
                'views': [[self.env.ref('dw_supplier_approval.view_manufacturing_document_wizard').id, 'form']],
                'target': 'new',

                'context': {
                    'default_homologation_id': self.id
                }
            }
        else:
            self.write({"state": "analyse"})

    def show_purchase_order(self):
        self.ensure_one()

        return {
            'name': 'Purchase Order',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'domain': [('homologation_id', '=', self.id)],
            'context': {
                'default_homologation_id': self.id
            }
            ,
            'views': [(False, 'tree'), (False, 'form')],
            'target': 'current',
        }

    def create_purchase_order(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'Manufacturing Document',
            'res_model': 'purchase.order',
            'views': [[self.env.ref('purchase.purchase_order_form').id, 'form']],

            'context': {
                'default_homologation_id': self.id,
                'default_partner_id': self.supplier_id.id,
                'default_order_line': [(0, 0, {'product_id': self.product_id.id,
                                               'name': self.product_id.name,
                                               'price_unit': 0.0,
                                               'product_uom': self.product_id.product_tmpl_id.uom_po_id.id,

                                               })]
            }
        }

    def button_prospection(self):
        self.write({"state": "prospection"})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'name' not in vals or vals['name'] == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('dw.homologation') or _('New')
        return super().create(vals_list)

    def action_to_audit(self):

        if self.rapport_expertise_attachment and self.rapport_expertise_file_name:
            self.env['documents.document'].create({
                'res_model': 'dw.homologation',
                'res_id': self.id,
                'name': self.rapport_expertise_file_name,
                'type': 'binary',
                'product_id': self.product_id.id if self.product_id else False,
                'partner_id': self.supplier_id.id if self.supplier_id else False,
                'datas': self.rapport_expertise_attachment,
                'folder_id': self.env.ref('dw_supplier_approval.folder_homologation').id,
            })
        self.write({"state": "audit"})

    def action_to_lot_validation_or_qualification(self):
        if self.rapport_audit_attachment and self.rapport_audit_file_name:
            self.env['documents.document'].create({
                'res_model': 'dw.homologation',
                'res_id': self.id,
                'name': self.rapport_audit_file_name,
                'type': 'binary',
                'product_id': self.product_id.id if self.product_id else False,
                'partner_id': self.supplier_id.id if self.supplier_id else False,
                'datas': self.rapport_audit_attachment,
                'folder_id': self.env.ref('dw_supplier_approval.folder_homologation').id,
            })

        if self.lot_validation:
            self.write({"state": "lot_validation"})
        else:
            self.write({"state": "qualification"})

    def action_to_qualification(self):
        if self.fichier_stabilite_attachment and self.fichier_stabilite_file_name:
            self.env['documents.document'].create({
                'res_model': 'dw.homologation',
                'res_id': self.id,
                'name': self.fichier_stabilite_file_name,
                'type': 'binary',
                'product_id': self.product_id.id if self.product_id else False,
                'partner_id': self.supplier_id.id if self.supplier_id else False,
                'datas': self.fichier_stabilite_attachment,
                'folder_id': self.env.ref('dw_supplier_approval.folder_homologation').id,
            })
        self.write({"state": "qualification"})

    def action_homologate(self):
        self.write({"state": "homologue"})

    def action_cancel(self):
        self.write({"state": "cancel"})

    def show_documents(self):
        self.ensure_one()
        return {
            'res_model': 'documents.document',
            'type': 'ir.actions.act_window',
            'name': _("%(market_name)s homologations's Documents", market_name=self.name),
            'domain': [
                ('res_model', '=', 'dw.homologation'), ('res_id', '=', self.id),
            ],
            'view_mode': 'kanban,tree,form',

            'context': {'default_res_model': 'dw.homologation', 'default_res_id': self.id,
                        'default_partner_id': self.supplier_id.id if self.supplier_id else False,
                        'default_product_id': self.product_id.id if self.product_id else False,
                        'limit_folders_to_lead': True},
        }
