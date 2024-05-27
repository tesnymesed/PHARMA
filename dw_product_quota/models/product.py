from odoo import models


class DwProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_view_allowed_quotas(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("dw_product_quota.dw_product_quota_action")
        action['domain'] = [('product_id.product_tmpl_id', '=', self.id)]
        action['context'] = {
            'default_product_tmpl_id': self.id,
            'default_company_id': (self.company_id or self.env.company).id,
        }
        if self.product_variant_count == 1:
            action['context'].update({
                'default_product_id': self.product_variant_id.id,
            })
        return action


class DwProduct(models.Model):
    _inherit = 'product.product'

    def action_view_allowed_quotas(self):
        self.ensure_one()
        action = self.product_tmpl_id.action_view_allowed_quotas()
        action['domain'] = [('product_id', '=', self.id)]
        action['context'].update({
            'default_product_id': self.id,
            'set_product_readonly': True,
        })
        return action
