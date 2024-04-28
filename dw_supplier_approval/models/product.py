# -*- coding:utf-8 -*-

from odoo import fields, models, api, _


class DwProductTemplate(models.Model):
    _inherit = 'product.template'
    homologue = fields.Boolean(
        'approval required',
        default=False
    )

    def action_show_homologations(self):
        return ({
            'res_model': 'dw.homologation',
            'type': 'ir.actions.act_window',
            'name': _("%(product_name)s's homologation", product_name=self.name),

            'domain': [
                ('product_id.product_tmpl_id', '=', self.id),
            ],
            'view_mode': 'tree,form',

            'context': {"create": 0},
        })


class DwProduct(models.Model):
    _inherit = 'product.product'
    homologue = fields.Boolean(
        'approval required',
        default=False
    )
    number_fournisseur = fields.Integer('Number of fournisseur', compute="_compute_number_fournisseur", store=0)
    homologation_ids = fields.One2many("dw.homologation", 'product_id', string="Homologation")

    def action_show_homologations(self):
        return ({
            'res_model': 'dw.homologation',
            'type': 'ir.actions.act_window',
            'name': _("%(product_name)s's homologation", product_name=self.name),

            'domain': [
                ('product_id', '=', self.id),
            ],
            'view_mode': 'tree,form',

            'context': {"create": 0},
        })

    # @api.depends('homologation_ids')
    def _compute_number_fournisseur(self):
        for record in self:
            record.number_fournisseur = len(record.homologation_ids.filtered(
                lambda homologation: homologation.state == 'homologue'))

    def _prepare_market_line(self):

        vals_dict = [
            (0, 0, {'product_id': self.id})]
        return vals_dict

    def _prepare_market(self):
        return {
            'company_id': self.company_id.id if self.company_id else False,
            'dw_homologate': True,
            "market_line_ids": self._prepare_market_line()
        }

    def action_launch_market(self):
        market_list = []
        DwMarket = self.env['dw.market']
        for rec in self:
            market_list.append(rec._prepare_market())
        DwMarket.create(market_list)
