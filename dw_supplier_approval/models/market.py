# -*- coding:utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class DwMarketLine(models.Model):
    _inherit = 'dw.market.line'

    product_id = fields.Many2one(
        domain=['|', '|', ('homologue', '=', True), ('categ_id.homologue', '=', True),
                ('product_tmpl_id.homologue', '=', True), ('purchase_ok', '=', True)],

    )

    line_homlogated = fields.Boolean(default=False)
    # def action_done(self):
    #     market_id = self.market_id
    #     if market_id.dw_homologate:
    #         if market_id.market_type_id and market_id.market_type_id.forced_nbr_supplier and len(
    #                 self.supplier_ids) < market_id.market_type_id.nbr_supplier:
    #             raise ValidationError(
    #                 _('The number of the Homologated  supplier must be greater than %(nbr_supplier)s.!',
    #                   nbr_supplier=market_id.market_type_id.nbr_supplier)
    #             )
    #
    #         return {
    #             'type': 'ir.actions.act_window',
    #             'name': 'Market Document',
    #             'res_model': 'dw.homologate.market.wizard',
    #             'views': [[self.env.ref('dw_supplier_approval.dw_homologate_market_form_view').id, 'form']],
    #             'target': 'new',
    #
    #             'context': {
    #                 'default_line_id': self.id
    #             }
    #         }


class DwMarket(models.Model):
    _inherit = 'dw.market'

    state = fields.Selection(selection_add=[
        ('homologation_cosultation', 'Approval/consultation')
    ])
    dw_homologate = fields.Boolean(string="This market is used for homologation", default=True)

    homologation_ids = fields.Many2many("dw.homologation", 'market_id', string="Homologation")
    supplier_homologuer_ids = fields.Many2many(
        'res.partner',
        compute="_compute_homolgated_supplier"
    )

    len_supplier_homologated_market = fields.Integer("Length Market supplier Approved", store=0,
                                                     compute="compute_len_supplier_homologated_market")

    @api.depends('supplier_homologuer_ids')
    def compute_len_supplier_homologated_market(self):
        for record in self:
            record.len_supplier_homologated_market = len(record.supplier_homologuer_ids)

    @api.depends('supplier_ids')
    def _compute_homolgated_supplier(self):
        for record in self:
            record.supplier_homologuer_ids = record.homologation_ids.filtered(
                lambda homologation: homologation.state == 'homologue').mapped("supplier_id")

    def action_done(self):
        if not self.dw_for_homologation:
            return super(DwMarket, self).action_done()

        if self.market_type_id and self.market_type_id.forced_nbr_supplier and self.len_supplier_homologated_market < self.market_type_id.nbr_supplier:
            raise ValidationError(
                _('The number of Homologated suppliers must be greater than %(nbr_supplier)s.',
                  nbr_supplier=self.market_type_id.nbr_supplier)
            )

        return {
            'type': 'ir.actions.act_window',
            'name': 'Market Document',
            'res_model': 'dw.attribute.market.wizard',
            'views': [[self.env.ref('dw_procurement.dw_attribute_market_form_view').id, 'form']],
            'target': 'new',
            'context': {
                'default_market_id': self.id
            }
        }

    def action_show_homologations(self):
        return ({
            'res_model': 'dw.homologation',
            'type': 'ir.actions.act_window',
            'name': _("%(market_name)s's homologation", market_name=self.name),

            'domain': [
                ('market_ids', 'in', self.id),
            ],
            'view_mode': 'tree,form',

            'context': {'default_market_id': self.id, "create": 0},
        })
