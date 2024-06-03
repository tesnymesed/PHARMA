from odoo import fields, models, _


class DWProductQuotaType(models.Model):
    _name = 'dw.product.quota.type'
    _description = "Product's Allowed Quota Type"

    name = fields.Char(string='Type', copy=False, required=True, default=_('New'))

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
