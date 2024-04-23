# -*- coding:utf-8 -*-

from odoo import fields, models,api


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
    number_fournisseur = fields.Integer('Number of fournisseur',compute="_compute_number_fournisseur",store=True)
    @api.depends('seller_ids')
    def _compute_number_fournisseur(self):
        if self.seller_ids:
         self.number_fournisseur=len(self.seller_ids)
        else :
            self.number_fournisseur = False
    def action_launch_market(self):
        for res in self :
            market = self.env['dw.market'].create({
                'name': 'new market',
                'product_ids':[(4,res.id)]})