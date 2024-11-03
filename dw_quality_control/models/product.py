from odoo import models, api, fields


class QualityProductTemplate(models.Model):
    _inherit = 'product.template'

    quality_model_id = fields.Many2one('quality.check.product.model', string='Quality Model')
    auto_qc_gen = fields.Boolean(string="auto-generated quality check.")


class QualityProductProduct(models.Model):
    _inherit = 'product.product'

    quality_model_id = fields.Many2one('quality.check.product.model', string='Quality Model')
    auto_qc_gen = fields.Boolean(string="auto-generated quality check.")
