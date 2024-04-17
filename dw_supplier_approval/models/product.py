# -*- coding:utf-8 -*-

from odoo import fields, models


class DwProductTemplate(models.Model):
    _inherit = 'product.template'
    homologue = fields.Boolean(
        'homologué',
        default=False
    )
class DwProduct(models.Model):
    _inherit = 'product.product'
    homologue = fields.Boolean(
        'homologué',
        default=False
    )