from odoo import models, fields


class QualityCheckLine(models.Model):
    _name = "quality.check.line"

    name = fields.Char()
    reference = fields.Char()
    standards = fields.Char()
    result = fields.Char()
    quality_check_id = fields.Many2one(
        'quality.check'
    )
