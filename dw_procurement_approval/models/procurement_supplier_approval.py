# -*- coding:utf-8 -*-

from odoo import fields, models, api, _


class ProcurementSupplierApproval(models.Model):
    _inherit = 'procurement.supplier.approval'

    market_ids = fields.Many2many('procurement.market.dw', string='Market')
    consultation_ids = fields.One2many("procurement.dw.consultation", "approval_id", string="Consultation")

    def action_market_assign(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'link to market',
            'res_model': 'procurement.market.dw.assign.wizard',
            'views': [[self.env.ref('dw_procurement_approval.dw_market_assign_form_view').id, 'form']],
            'target': 'new',

            'context': {
                'default_approval_id': self.id
            }
        }

    def show_purchase_order(self):
        self.ensure_one()

        return {
            'name': 'Purchase Order',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'domain': [('approval_id', '=', self.id)],
            'context': {
                'default_approval_id': self.id
            }
            ,
            'views': [(False, 'tree'), (False, 'form')],
            'target': 'current',
        }

    def create_purchase_order(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'BC Echantillion',
            'res_model': 'purchase.order',
            'views': [[self.env.ref('purchase.purchase_order_form').id, 'form']],

            'context': {'create': 0,
                        'default_approval_id': self.id,
                        'default_partner_id': self.supplier_id.id,
                        'default_order_line': [(0, 0, {'product_id': self.product_id.id,
                                                       'name': self.product_id.name,
                                                       'price_unit': 0.0,
                                                       'product_uom': self.product_id.product_tmpl_id.uom_po_id.id,

                                                       })]
                        }
        }

    def action_lunch_consultation(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Approval Consult',
            'res_model': 'procurement.consult.approval',
            'views': [[self.env.ref('dw_procurement_approval.approval_consult_form_view').id, 'form']],
            'target': 'new',

            'context': {
                'default_approval_id': self.id
            }
        }



    def action_show_consultations(self):
        return ({
            'res_model': 'procurement.dw.consultation',
            'type': 'ir.actions.act_window',
            'name': _("%(approval_name)s's Consultations", approval_name=self.name),

            'domain': [
                ('approval_id', '=', self.id),
            ],
            'view_mode': 'tree,form',

            'context': {'create': False},
        })

    def action_show_market(self):
        return ({
            'res_model': 'procurement.market.dw',
            'type': 'ir.actions.act_window',
            'name': _("%(market_name)s's Market", market_name=self.name),

            'domain': [
                ('approval_ids', 'in', self.id),
            ],
            'view_mode': 'tree,form',

            'context': {"create": 0},
        })
