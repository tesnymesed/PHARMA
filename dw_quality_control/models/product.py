from odoo import models, api, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    quality_model_id = fields.Many2one('quality.check.product.model', string='Quality Model')