from odoo import fields, models, _, api


class DocumentWizard(models.TransientModel):
    _name = "dw.document.wizard"
    name = fields.Char('name', compute="_compute_name")
    manufacturing_document_attachment = fields.Binary(string="Document fabriquant")
    manufacturing_file_name = fields.Char(string='File name')
    homologation_id = fields.Many2one("dw.homologation", string="Homologation")

    @api.depends('manufacturing_file_name')
    def _compute_name(self):
        for record in self:
            if record.manufacturing_file_name:
                record.name = record.manufacturing_file_name

    def action_confirm(self):
        if self.manufacturing_document_attachment and self.manufacturing_file_name:
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
