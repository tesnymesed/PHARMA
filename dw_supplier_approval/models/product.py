# -*- coding:utf-8 -*-

from odoo import fields, models, api, _
from datetime import date


class DwProductTemplate(models.Model):
    _inherit = 'product.template'
    need_approval = fields.Boolean(
        'approval required',
        default=False
    )

    def action_show_approvals(self):
        return ({
            'res_model': 'procurement.supplier.approval',
            'type': 'ir.actions.act_window',
            'name': _("%(product_name)s's approval", product_name=self.name),

            'domain': [
                ('product_id.product_tmpl_id', '=', self.id),
            ],
            'view_mode': 'tree,form',

            'context': {"create": 0},
        })


class DwProduct(models.Model):
    _inherit = 'product.product'
    need_approval = fields.Boolean(
        'approval required',
        default=False
    )
    number_supplier = fields.Integer('Number of supplier', compute="_compute_number_supplier")
    number_supplier2 = fields.Integer('Number of supplier', compute="_compute_number_supplier2", store=True)

    approval_ids = fields.One2many("procurement.supplier.approval", 'product_id', string="approval")

    has_blacklisted_supplier = fields.Boolean('Blacklisted', compute="_compute_has_blacklisted")
    has_blacklisted_supplier2 = fields.Boolean('Blacklisted', related="has_blacklisted_supplier", store=True)

    expired_approval = fields.Boolean('Expired approval', compute="_compute_expired_approval")
    expired_approval2 = fields.Boolean('Expired approval', related="expired_approval", store=True)

    expired_contract = fields.Boolean('Expired contract', compute="_compute_expired_contract")
    expired_contract2 = fields.Boolean('Expired contract', related="expired_contract", store=True)
    need_priority = fields.Selection([
        ('0', 'No priority'),
        ('1', 'Low priority'),
    ('2', 'Medium priority'),
    ('3', 'High priority'),
    ], string="Need Priority", default='1')

    @api.depends('number_supplier')
    def _compute_number_supplier2(self):
        for record in self:
            record.number_supplier2 = record.number_supplier

    def action_show_approvals(self):
        return ({
            'res_model': 'procurement.supplier.approval',
            'type': 'ir.actions.act_window',
            'name': _("%(product_name)s's approval", product_name=self.name),

            'domain': [
                ('product_id', '=', self.id),
            ],
            'view_mode': 'tree,form',

            'context': {"create": 0},
        })

    # @api.depends('approval_ids')
    def _compute_number_supplier(self):
        for record in self:
            record.number_supplier = len(record.approval_ids.filtered(
                lambda approval: approval.state == 'approval'))


    def diff_month(self, d1, d2):
        return (d1.year - d2.year) * 12 + d1.month - d2.month

    def _compute_expired_contract(self):
        today = date.today()

        for record in self:
            record.expired_contract = True if any(
                seller.purchase_requisition_id and seller.purchase_requisition_id.date_end and
                self.diff_month(seller.purchase_requisition_id.date_end, today) <= 18 for seller in
                record.seller_ids) else False

    def _compute_expired_approval(self):
        today = date.today()
        for record in self:
            record.expired_approval = True if any(approval.end_date and approval.state == 'approval' and
                                                      self.diff_month(approval.end_date, today) <= 18 for
                                                      approval in record.approval_ids) else False

    def _compute_has_blacklisted(self):
        for record in self:
            blacklist1 = True if any(
                approval.supplier_id.is_blacklisted == True and approval.state == 'approval' for approval
                in record.approval_ids) else False
            blacklist2 = True if any(
                seller.partner_id.is_blacklisted == True for seller in
                record.seller_ids) else False
            if blacklist1 or blacklist2:
                record.has_blacklisted_supplier = True
            else:
                record.has_blacklisted_supplier = False
