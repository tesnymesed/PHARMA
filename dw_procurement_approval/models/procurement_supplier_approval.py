# -*- coding:utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class ProcurementSupplierApproval(models.Model):
    _inherit = 'procurement.supplier.approval'



    consultation_ids = fields.One2many("procurement.dw.consultation", "approval_id", string="Consultation")

    def market_assign(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Market assign',
            'res_model': 'procurement.market.dw.assign.wizard',
            'views': [[self.env.ref('dw_supplier_approval.dw_market_assign_form_view').id, 'form']],
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
        self.consultation_id = self.env['procurement.dw.consultation'].create(self._prepare_consultation())
        if self.consultation_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Consultation',
                'res_model': 'procurement.dw.consultation',
                'views': [[self.env.ref('dw_procurement.dw_consultation_form_view').id, 'form']],
                'res_id': self.consultation_id.id,
                'context': {"create": 0},
            }
    

    def action_create_consultation(self):
        DwConsultatio = self.env['procurement.dw.consultation']

        for record in self:
            if record.state != "approval":
                raise ValidationError(
                    _('This supplier %(supplier_name)s is not approval for this product %(product_name)s .!',
                      supplier_name=record.supplier_id.name, product_name=record.product_id.name)
                )
            record.consultation_id = DwConsultatio.create(record._prepare_consultation())

 
    def _prepare_criteria_line_consultation(self, market_id):
        if not market_id:
            return []
        vals_dict = [
            (0, 0, {'criteria_id': criteria.id}) for criteria in market_id.market_criteria_ids]
        return vals_dict

    def _prepare_consultation(self):
        return {
            'supplier_id': self.supplier_id.id if self.supplier_id else False,
            'dw_supplier_nature': self.dw_supplier_nature if self.supplier_id else False,
            'product_id': self.product_id.id if self.product_id else False,
            'market_id': self.market_ids.active_id if self.market_ids else False,
            'approval_id': self.id,
            'qty': self.qty,
            'company_id': self.company_id.id if self.company_id else False,
            "criteria_line_ids": self._prepare_criteria_line_consultation(self.market_id)
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