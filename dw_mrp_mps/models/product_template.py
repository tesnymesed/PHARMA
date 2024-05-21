from odoo import api, fields, models


class DwProductTemplate(models.Model):
    _inherit = 'product.template'

    dw_purchase_lead = fields.Float(
        "Computed Purchase Lead Time",  default=0.0, help="Lead days for each purchase operation (Used in MPS).",
        compute='_compute_lead_time', inverse='_inverse_lead_time',
    )

    dw_set_lead_time = fields.Float(
        "Set Purchase Lead Time", default=-1.0, help="Set Lead days for each purchase operation (Set by User).",
        store=True
    )

    @api.depends('company_id.manufacturing_lead', 'dw_set_lead_time')
    def _compute_lead_time(self):
        # TODO: Take into consideration whether use_product_lead_time is enabled or not
        # _use_product_lead = self.env['ir.config_parameter'].sudo().get_param('dw_mrp.dw_use_product_lead')
        # if bool(_use_product_lead):
        #     pass
        for record in self:
            if record.dw_set_lead_time > 0.0:
                _delay = record.dw_set_lead_time
            else:
                manufacturing_lead = self.env['ir.config_parameter'].sudo().get_param('dw_mrp.manufacturing_lead')
                try:
                    _delay = round(float(manufacturing_lead), 2)
                except ValueError as e:
                    _delay = 0.0

            record.dw_purchase_lead = _delay

    def _inverse_lead_time(self):
        for record in self:
            print(record.dw_purchase_lead)
            print(record.dw_set_lead_time)
            record.dw_set_lead_time = record.dw_purchase_lead
