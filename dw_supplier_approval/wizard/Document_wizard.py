from odoo import fields, models, _, api


class DocumentWizard(models.TransientModel):
    _name = "dw.document.wizard"
    name = fields.Char('name', compute="_compute_name")
    manufacturing_document_attachment = fields.Binary(string="Document fabriquant")
    manufacturing_file_name = fields.Char(string='File name')
    approval_id = fields.Many2one("procurement.supplier.approval", string="approval")
    state_approval = fields.Selection(
        selection=[
            ('prospecting', 'prospecting'),
            ('analyse', 'Analyse'),
            ('audit', 'Audit'),
            ('lot_validation', 'Lot Validation'),
            ('qualification', 'Qualification'),
            ('approval', 'approved'),
            ('cancel', 'Canceled')
        ],
        string="State",

        related="approval_id.state"
        ,
        store="1",
    )

    rapport_expertise_attachment = fields.Binary(string="Expert report")
    rapport_expertise_file_name = fields.Char(string='File name')

    rapport_technique_attachment = fields.Binary(string="Technical control report")
    rapport_technique_name = fields.Char(string='File name')

    rapport_audit_attachment = fields.Binary(string="Supplier audit report")
    rapport_audit_file_name = fields.Char(string='File name')

    stability_file_attachment = fields.Binary(string="Fichier de stabilité")
    stabilite_file_name = fields.Char(string='File name')

    Pre_eval_quest_attachment = fields.Binary(string="Pre-evaluation questionnaire")
    Pre_eval_quest_name = fields.Char(string='File name')

    def action_Pre_eval_quest(self):
        if self.Pre_eval_quest_attachment and self.Pre_eval_quest_name:
            self.env['documents.document'].create({
                'res_model': 'procurement.supplier.approval',
                'res_id': self.approval_id.id,
                'name': self.Pre_eval_quest_name,
                'type': 'binary',
                'product_id': self.approval_id.product_id.id if self.approval_id and self.approval_id.product_id else False,
                'partner_id': self.approval_id.supplier_id.id if self.approval_id and self.approval_id.supplier_id else False,
                'datas': self.Pre_eval_quest_attachment,
                'folder_id': self.env.ref('dw_supplier_approval.folder_supplier_approval').id,
            })

    def action_exper_techn_report(self):
        if self.rapport_expertise_attachment and self.rapport_expertise_file_name:
            self.env['documents.document'].create({
                'res_model': 'procurement.supplier.approval',
                'res_id': self.approval_id.id,
                'name': self.rapport_expertise_file_name,
                'type': 'binary',
                'product_id': self.approval_id.product_id.id if self.approval_id and self.approval_id.product_id else False,
                'partner_id': self.approval_id.supplier_id.id if self.approval_id and self.approval_id.supplier_id else False,
                'datas': self.rapport_expertise_attachment,
                'folder_id': self.env.ref('dw_supplier_approval.folder_supplier_approval').id,
            })
        if self.rapport_technique_attachment and self.rapport_technique_name:
            self.env['documents.document'].create({
                'res_model': 'procurement.supplier.approval',
                'res_id': self.approval_id.id,
                'name': self.rapport_technique_name,
                'display_name': self.rapport_technique_name,
                'type': 'binary',
                'product_id': self.approval_id.product_id.id if self.approval_id and self.approval_id.product_id else False,
                'partner_id': self.approval_id.supplier_id.id if self.approval_id and self.approval_id.supplier_id else False,
                'datas': self.rapport_technique_attachment,
                'folder_id': self.env.ref('dw_supplier_approval.folder_supplier_approval').id,
            })

    @api.depends('manufacturing_file_name')
    def _compute_name(self):
        for record in self:
            if record.manufacturing_file_name:
                record.name = record.manufacturing_file_name

    def action_manufacturing(self):
        if self.manufacturing_document_attachment and self.manufacturing_file_name and self.state_approval == 'prospecting':
            self.env['documents.document'].create({
                'res_model': 'procurement.supplier.approval',
                'res_id': self.approval_id.id,
                'name': self.manufacturing_file_name,
                'display_name': self.manufacturing_file_name,
                'type': 'binary',
                'product_id': self.approval_id.product_id.id if self.approval_id and self.approval_id.product_id else False,
                'partner_id': self.approval_id.supplier_id.id if self.approval_id and self.approval_id.supplier_id else False,
                'datas': self.manufacturing_document_attachment,
                'folder_id': self.env.ref('dw_supplier_approval.folder_supplier_approval').id,
            })
            self.approval_id.write({"state": "analyse"})

    def action_audit(self):
        if self.rapport_audit_attachment and self.rapport_audit_file_name and self.state_approval == 'audit':
            self.env['documents.document'].create({
                'res_model': 'procurement.supplier.approval',
                'res_id': self.approval_id.id,
                'name': self.rapport_audit_file_name,
                'type': 'binary',
                'product_id': self.approval_id.product_id.id if self.approval_id and self.approval_id.product_id else False,
                'partner_id': self.approval_id.supplier_id.id if self.approval_id and self.approval_id.supplier_id else False,
                'datas': self.rapport_audit_attachment,
                'folder_id': self.env.ref('dw_supplier_approval.folder_supplier_approval').id,
            })

    def action_stability(self):
        if self.stability_file_attachment and self.stabilite_file_name and self.state_approval == 'lot_validation':
            self.env['documents.document'].create({
                'res_model': 'procurement.supplier.approval',
                'res_id': self.approval_id.id,
                'name': self.stabilite_file_name,
                'type': 'binary',
                'product_id': self.approval_id.product_id.id if self.approval_id and self.approval_id.product_id else False,
                'partner_id': self.approval_id.supplier_id.id if self.approval_id and self.approval_id.supplier_id else False,
                'datas': self.stability_file_attachment,
                'folder_id': self.env.ref('dw_supplier_approval.folder_supplier_approval').id,
            })
