# -*- coding:utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class DwMarketLine(models.Model):
    _inherit = 'procurement.market.dw.line'

    line_approved = fields.Boolean(default=False)

    def action_done(self):
        market_id = self.market_id
        if market_id.for_approval:
            if market_id.market_type_id and market_id.market_type_id.forced_nbr_supplier and len(
                    self.supplier_ids) < market_id.market_type_id.nbr_supplier:
                raise ValidationError(
                    _('The number of the approval  supplier must be greater than %(nbr_supplier)s.!',
                      nbr_supplier=market_id.market_type_id.nbr_supplier)
                )

            return {
                'type': 'ir.actions.act_window',
                'name': 'Market Document',
                'res_model': 'dw.homologate.market.wizard',
                'views': [[self.env.ref('dw_supplier_approval.for_approval_market_form_view').id, 'form']],
                'target': 'new',

                'context': {
                    'default_line_id': self.id
                }
            }


class DwMarket(models.Model):
    _inherit = 'procurement.market.dw'

    state = fields.Selection(selection_add=[
        ('approval_consultation', 'Approval/consultation')
    ])
    for_approval = fields.Boolean(string="This market is used for approval", default=True)

    approval_ids = fields.Many2many("procurement.supplier.approval", 'market_id', string="approval")
    supplier_approval_ids = fields.Many2many(
        'res.partner',
        compute="_compute_approval_supplier"
    )

    len_supplier_approval_market = fields.Integer("Length Market supplier Approved", store=0,
                                                  compute="compute_len_supplier_approval_market")

    @api.depends('supplier_approval_ids')
    def compute_len_supplier_approval_market(self):
        for record in self:
            record.len_supplier_approval_market = len(record.supplier_approval_ids)

    @api.depends('supplier_ids')
    def _compute_approval_supplier(self):
        for record in self:
            record.supplier_approval_ids = record.approval_ids.filtered(
                lambda approval: approval.state == 'approval').mapped("supplier_id")

    def action_confirm(self):
        res = super(DwMarket, self).action_confirm()
        if self.for_approval:
            self.write({"state": "approval_consultation"})

        return res

    def action_done(self):
        if not self.for_approval:
            return super(DwMarket, self).action_done()

        if self.market_type_id and self.market_type_id.forced_nbr_supplier and self.len_supplier_approval_market < self.market_type_id.nbr_supplier:
            raise ValidationError(
                _('The number of approval suppliers must be greater than %(nbr_supplier)s.',
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

    def action_show_approvals(self):
        return ({
            'res_model': 'procurement.supplier.approval',
            'type': 'ir.actions.act_window',
            'name': _("%(market_name)s's approval", market_name=self.name),

            'domain': [
                ('market_ids', 'in', self.id),
            ],
            'view_mode': 'tree,form',

            'context': {'default_market_id': self.id, "create": 0},
        })
