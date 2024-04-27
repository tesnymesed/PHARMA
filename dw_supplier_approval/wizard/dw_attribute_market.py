from odoo import fields, models, _, api


class DwAttributeMarket(models.TransientModel):
    _name = "dw.attribute.market.wizard"
    market_id = fields.Many2one("dw.market", "Market")
    consultation_id = fields.Many2one("dw.consultation", "Consultation",
                                      domain="[('market_id','=',market_id),('state','=','consulted')]")

    def action_confirm(self):
        market_id = self.market_id
        consultation_id = self.consultation_id
        market_id.write({"state": "done"})

        return {
            'type': 'ir.actions.act_window',
            'name': 'Attribution',
            'res_model': 'purchase.requisition',
            'views': [[self.env.ref('purchase_requisition.view_purchase_requisition_form').id, 'form']],

            'context': {'create': 0,
                        'default_vendor_id': consultation_id.supplier_id.id,
                        'default_market_id': market_id.id,
                        'default_line_ids': [(0, 0, {'product_id': consultation_id.product_id.id,
                                                     'price_unit': 0.0,

                                                     })]
                        }
        }
