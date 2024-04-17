
from odoo import api, fields, models


class DocumentLine(models.Model):
    _name = "dw.document.line"

    dw_name = fields.Char(string="Name")
    dw_attachment = fields.Binary(string="Attachment")
    file_name = fields.Char(string='File name')
    homologation_id = fields.Many2one('dw.homologation')
    #
    # def create(self, vals):
    #     res= super(DocumentLine, self).create(vals)
    #     if res.file_name  and res.dw_attachment and  res.homologation_id:
    #
    #         pg_recorded = self.env['documents.document'].create({
    #             'res_model': 'dw.homologation',
    #             'res_id': res.homologation_id,
    #             'name': res.file_name,
    #             'type': 'binary',
    #             'partner_id': res.homologation_id.supplier_id.id,
    #             'datas': res.dw_attachment,
    #             'folder_id': self.env.ref('dw_supplier_approval.folder_homologation').id,
    #
    #
    #         })
    #
    #     return res
    #
    #
    # def write(self, vals):
    #     res = super(DocumentLine, self).write(vals)
    #     if self.file_name and self.dw_attachment and self.dw_crm_lead_id:
    #         pg_recorded = self.env['documents.document'].create({
    #             'res_model': 'dw.homologation',
    #             'res_id': res.homologation_id,
    #             'name': res.file_name,
    #             'type': 'binary',
    #             'partner_id': res.homologation_id.supplier_id.id,
    #             'datas': res.dw_attachment,
    #             'folder_id': self.env.ref('dw_supplier_approval.folder_homologation').id,
    #
    #         })
    #
    #     return res