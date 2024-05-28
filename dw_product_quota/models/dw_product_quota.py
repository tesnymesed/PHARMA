from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from .utils import _domain_supply_products


class DWProductPurchaseQuota(models.Model):
    _name = 'dw.product.quota'
    _description = "Product's Allowed Quotas"

    name = fields.Char(string='Reference', copy=False, required=True, default=_('New'))

    quota = fields.Float(string='Quota', required=True)
    date_start = fields.Date(string='Quota Start Date', required=True)
    date_end = fields.Date(string='Quota End Date', required=True)

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('expired', 'Expired'),
            ('cancelled', 'Cancelled'),

        ], default='draft')

    product_id = fields.Many2one('product.product', string='Product', required=True, ondelete='cascade',
                                 domain=lambda self: _domain_supply_products())

    uom_id = fields.Many2one('uom.uom', related='product_id.uom_id', readonly=True)

    type_id = fields.Many2one('dw.product.quota.type', string='Quota Type', required=True)

    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.type_id.company_id or self.env.company, readonly=False)

    @api.constrains('quota')
    def _check_quota(self):
        for record in self:
            if record.quota <= 0:
                raise ValidationError("Quota must be greater than 0.")

    @api.constrains('date_end')
    def _check_quota_expiration_date(self):
        for record in self:
            if record.date_end < date.today():
                raise ValidationError("Quota expiration date must be in the future.")

    @api.constrains('date_start', 'date_end')
    def _check_quota_dates(self):
        for record in self:
            if record.date_start > record.date_end:
                raise ValidationError("Quota end date must be after the start date.")
            # if record.quota_start < date.today():
            #     raise ValidationError("Quota start date must be in the future.")

    def action_confirm(self):
        self.write({
            'state': 'confirmed',
        })

    def action_cancel(self):
        self.write({
            'state': 'cancelled',
        })

    def action_draft(self):
        self.write({
            'state': 'draft',
        })
