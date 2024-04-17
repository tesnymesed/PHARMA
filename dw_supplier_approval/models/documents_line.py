
from odoo import api, fields, models


class DocumentLine(models.Model):
    _name = "dw.document.line"

    dw_name = fields.Char(string="Name")
    dw_attachment = fields.Binary(string="Attachment")
    file_name = fields.Char(string='File name')
    homologation_id = fields.Many2one('dw.homologation')
