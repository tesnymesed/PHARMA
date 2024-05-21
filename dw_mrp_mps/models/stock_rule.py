from odoo import models, _


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_lead_days(self, product, **values):
        """Add product lead time to the cumulative delay and cumulative description.
        """
        delays, delay_description = super()._get_lead_days(product, **values)

        buy_rule = self.filtered(lambda r: r.action == 'buy')

        if not buy_rule:
            return delays, delay_description

        buy_rule.ensure_one()

        _use_product_lead = self.env['ir.config_parameter'].sudo().get_param('dw_mrp.dw_use_product_lead')

        if bool(_use_product_lead):

            product_lead_time = product.dw_purchase_lead
            delays['total_delay'] += product_lead_time
            delays['product_lead_time'] += product_lead_time

            bypass_delay_description = self.env.context.get('bypass_delay_description')

            if not bypass_delay_description:
                delay_description.append((_('Product Lead Time'), _('+ %d day(s)', product_lead_time)))

        return delays, delay_description

