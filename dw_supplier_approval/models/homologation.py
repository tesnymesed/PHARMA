# -*- coding:utf-8 -*-

from odoo import fields, models,api,_
from odoo.exceptions import UserError, ValidationError

class DwHomologation(models.Model):
    _name = 'dw.homologation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    state = fields.Selection(
        selection=[
            ('prospection', 'Prospection'),
            ('analyse', 'Analyse'),
            ('audit', 'Audit'),
            ('lot_validation', 'Lot Validation'),
            ('qualification', 'Qualification'),
            ('homologue', 'Homologué'),
        ],
        string="State",
        default="prospection",
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
    )
    market_id = fields.Many2one('dw.market', string='Market')
    product_id = fields.Many2one(
        'product.product',
        check_company=True,
     related='market_id.product_id'
    )
    lot_validation = fields.Boolean('Lot Validation')
    documents_line_ids = fields.Many2many('dw.document.line', 'homologation_id')
    supplier_id = fields.Many2one(
        'res.partner',
        domain='[("is_supplier","=", True)]'
    )
    # address fields
    street = fields.Char(string="Address")
    street2 = fields.Char()
    zip = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', )
    country_code = fields.Char(related='country_id.code', string="Country Code")
    purchase_id = fields.Many2one("purchase.order",string="Purchase Order")

    manufacturing_document_attachment = fields.Binary(string="Document fabriquant")
    manufacturing_file_name = fields.Char(string='File name')

    rapport_expertise_attachment = fields.Binary(string="Document d\'expertise")
    rapport_expertise_file_name = fields.Char(string='File name')

    rapport_audit_attachment = fields.Binary(string="Document d\'audit")
    rapport_audit_file_name = fields.Char(string='File name')

    fichier_stabilite_attachment = fields.Binary(string="Fichier de stabilité")
    fichier_stabilite_file_name = fields.Char(string='File name')

    @api.onchange("supplier_id")
    def onchange_address(self):
       for homologation in self :
           homologation.street = homologation.supplier_id.street
           homologation.street2 = homologation.supplier_id.street2
           homologation.zip = homologation.supplier_id.zip
           homologation.city = homologation.supplier_id.city
           homologation.country_id = homologation.supplier_id.country_id
           homologation.state_id = homologation.supplier_id.state_id


    def action_to_analyse(self):
        for hom in self :
            if hom.supplier_id.dw_supplier_nature=='regroupeur':
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Manufacturing Document',
                    'res_model': 'dw.homologation',
                    'views': [[self.env.ref('dw_supplier_approval.view_manufacturing_document_wizard').id, 'form']],
                    'target': 'new',
                    'res_id': self.id,
                    # 'context': {
                    #     'default_id': self.id
                    # }
                }
        else : self.write({"state": "analyse"})
    def show_purchase_order(self):
        self.ensure_one()

        return {
            'name': 'Purchase Order',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'res_id': self.purchase_id.id,
            'view_mode': 'form',
            'domain': [('homologation_id', '=', self.id)],
            'views': [(False, 'form')],
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
                'default_order_line': [(0, 0, {'product_id':self.product_id.id,
                                               'name': self.product_id.name,
                                               'price_unit': 0.0,
                                               'product_uom': self.product_id.product_tmpl_id.uom_po_id.id,

                                               })]
            }
        }
    def action_confirm(self):
        active_id = self.env.context.get('active_id')
        record = self.env['dw.homologation'].browse(active_id)
        if record.manufacturing_document_attachment and record.manufacturing_file_name:

                pg_recorded = record.env['documents.document'].create({
                    'res_model': 'dw.homologation',
                    'res_id': record.id,
                    'name': record.manufacturing_file_name,
                    'type': 'binary',
                    'partner_id': record.supplier_id.id if record.supplier_id else False ,
                    'datas': record.manufacturing_document_attachment,
                    'folder_id': record.env.ref('dw_supplier_approval.folder_homologation').id,
                })
        self.write({"state": "analyse"})

    def action_to_audit(self):
        if self.purchase_id:

            if self.rapport_expertise_attachment and self.rapport_expertise_file_name:
                pg_recorded = self.env['documents.document'].create({
                    'res_model': 'dw.homologation',
                    'res_id': self.id,
                    'name': self.manufacturing_file_name,
                    'type': 'binary',
                    'partner_id': self.supplier_id.id if self.supplier_id else False,
                    'datas': self.manufacturing_document_attachment,
                    'folder_id': self.env.ref('dw_supplier_approval.folder_homologation').id,
                })
            self.write({"state": "audit"})
        else :
         raise ValidationError(_("Aucun bon de commande n'a été créé"))
    def action_to_lot_validation_or_qualification(self):
        if self.rapport_audit_attachment and self.rapport_audit_file_name:
            pg_recorded = self.env['documents.document'].create({
                'res_model': 'dw.homologation',
                'res_id': self.id,
                'name': self.rapport_audit_file_name,
                'type': 'binary',
                'partner_id': self.supplier_id.id if self.supplier_id else False,
                'datas': self.rapport_audit_attachment,
                'folder_id': self.env.ref('dw_supplier_approval.folder_homologation').id,
            })

        if self.lot_validation:
            self.write({"state": "lot_validation"})
        else :
            self.write({"state": "qualification"})
    def action_to_qualification(self):
        if self.fichier_stabilite_attachment and self.fichier_stabilite_file_name:
            pg_recorded = self.env['documents.document'].create({
                'res_model': 'dw.homologation',
                'res_id': self.id,
                'name': self.fichier_stabilite_file_name,
                'type': 'binary',
                'partner_id': self.supplier_id.id if self.supplier_id else False,
                'datas': self.fichier_stabilite_attachment,
                'folder_id': self.env.ref('dw_supplier_approval.folder_homologation').id,
            })
        self.write({"state": "qualification"})
    def action_homologuer(self):
        self.write({"state": "homologue"})
    def action_cancel(self):
        pass
    def show_documents(self):
        self.ensure_one()
        return {
            'res_model': 'documents.document',
            'type': 'ir.actions.act_window',
            'name': _("%(market_name)s homologations's Documents", market_name=self.market_id.name),
            'domain': [
                ('res_model', '=', 'dw.homologation'), ('res_id', '=', self.id),
            ],
            'view_mode': 'kanban,tree,form',

            'context': {'default_res_model': 'dw.homologation', 'default_res_id': self.id,'default_partner_id':self.supplier_id.id if self.supplier_id else False ,'limit_folders_to_lead': True},
        }

