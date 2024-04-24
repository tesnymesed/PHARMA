from odoo import fields, models, _, api


class DocumentWizard(models.TransientModel):
    _name = "dw.document.wizard"
    name = fields.Char('name', compute="_compute_name")
    manufacturing_document_attachment = fields.Binary(string="Document fabriquant")
    manufacturing_file_name = fields.Char(string='File name')
    homologation_id = fields.Many2one("dw.homologation", string="Homologation")
    state_homologation = fields.Selection(
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

        related ="homologation_id.state"
,
    store="1",
    )
    rapport_expertise_attachment = fields.Binary(string="Document d\'expertise")
    rapport_expertise_file_name = fields.Char(string='File name')

    rapport_audit_attachment = fields.Binary(string="Document d\'audit")
    rapport_audit_file_name = fields.Char(string='File name')

    fichier_stabilite_attachment = fields.Binary(string="Fichier de stabilité")
    stabilite_file_name = fields.Char(string='File name')
    @api.depends('manufacturing_file_name')
    def _compute_name(self):
        for record in self:
            if record.manufacturing_file_name:
                record.name = record.manufacturing_file_name

    def action_manufacturing(self):
        if self.manufacturing_document_attachment and self.manufacturing_file_name and self.state_homologation == 'prospection':
            self.env['documents.document'].create({
                'res_model': 'dw.homologation',
                'res_id': self.homologation_id.id,
                'name': self.manufacturing_file_name,
                'display_name': self.manufacturing_file_name,
                'type': 'binary',
                'product_id': self.homologation_id.product_id.id if self.homologation_id and self.homologation_id.product_id else False,
                'partner_id': self.homologation_id.supplier_id.id if self.homologation_id and self.homologation_id.supplier_id else False,
                'datas': self.manufacturing_document_attachment,
                'folder_id': self.env.ref('dw_supplier_approval.folder_homologation').id,
            })
            self.homologation_id.write({"state": "analyse"})



    def action_expertise(self):
        if self.rapport_expertise_attachment and self.rapport_expertise_file_name and self.state_homologation == 'analyse':
            self.env['documents.document'].create({
                'res_model': 'dw.homologation',
                'res_id': self.homologation_id.id,
                'name': self.rapport_expertise_file_name,
                'type': 'binary',
                'product_id': self.homologation_id.product_id.id if self.homologation_id and self.homologation_id.product_id else False,
                'partner_id': self.homologation_id.supplier_id.id if self.homologation_id and self.homologation_id.supplier_id else False,
                'datas': self.rapport_expertise_attachment,
                'folder_id': self.env.ref('dw_supplier_approval.folder_homologation').id,
            })
            self.homologation_id.write({"state": "audit"})
    def action_audit(self):
        if self.rapport_audit_attachment and self.rapport_audit_file_name and self.state_homologation == 'audit':
            self.env['documents.document'].create({
                'res_model': 'dw.homologation',
                'res_id': self.homologation_id.id,
                'name': self.rapport_audit_file_name,
                'type': 'binary',
                'product_id': self.homologation_id.product_id.id if self.homologation_id and self.homologation_id.product_id else False,
                'partner_id': self.homologation_id.supplier_id.id if self.homologation_id and self.homologation_id.supplier_id else False,
                'datas': self.rapport_audit_attachment,
                'folder_id': self.env.ref('dw_supplier_approval.folder_homologation').id,
            })

            if self.homologation_id.lot_validation:
                self.homologation_id.write({"state": "lot_validation"})
            else:
                self.homologation_id.write({"state": "qualification"})
    def action_stability(self):
        if self.fichier_stabilite_attachment and self.stabilite_file_name and self.state_homologation == 'lot_validation':
            self.env['documents.document'].create({
                'res_model': 'dw.homologation',
                'res_id': self.homologation_id.id,
                'name': self.stabilite_file_name,
                'type': 'binary',
                'product_id': self.homologation_id.product_id.id if self.homologation_id and self.homologation_id.product_id else False,
                'partner_id': self.homologation_id.supplier_id.id if self.homologation_id and self.homologation_id.supplier_id else False,
                'datas': self.fichier_stabilite_attachment,
                'folder_id': self.env.ref('dw_supplier_approval.folder_homologation').id,
            })
            self.homologation_id.write({"state": "qualification"})
