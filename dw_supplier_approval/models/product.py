# -*- coding:utf-8 -*-

from odoo import fields, models, api, _
from datetime import date
from dateutil.relativedelta import relativedelta


class DwProductTemplate(models.Model):
    _inherit = 'product.template'
    homologue = fields.Boolean(
        'approval required',
        default=False
    )

    def action_show_homologations(self):
        return ({
            'res_model': 'dw.homologation',
            'type': 'ir.actions.act_window',
            'name': _("%(product_name)s's homologation", product_name=self.name),

            'domain': [
                ('product_id.product_tmpl_id', '=', self.id),
            ],
            'view_mode': 'tree,form',

            'context': {"create": 0},
        })


class DwProduct(models.Model):
    _inherit = 'product.product'
    homologue = fields.Boolean(
        'approval required',
        default=False
    )
    number_fournisseur = fields.Integer('Number of fournisseur', compute="_compute_number_fournisseur", store=True)
    number_fournisseur2 = fields.Integer('Number of fournisseur', related="number_fournisseur", store=True)

    homologation_ids = fields.One2many("dw.homologation", 'product_id', string="Homologation")
    homologation_ids = fields.One2many("dw.homologation", 'product_id', string="Homologation")

    has_backliested_supplier = fields.Boolean('Blacklisted', compute="_compute_has_blacklisted")
    has_backliested_supplier2 = fields.Boolean('Blacklisted', related="has_backliested_supplier", store=True)

    expired_homologation = fields.Boolean('Expired homologation', compute="_compute_expired_homologation")
    expired_homologation2 = fields.Boolean('Expired homologation', related="expired_homologation", store=True)

    expired_contract = fields.Boolean('Expired contract', compute="_compute_expired_contract")
    expired_contract2 = fields.Boolean('Expired contract', related="expired_contract", store=True)
    def action_show_homologations(self):
        return ({
            'res_model': 'dw.homologation',
            'type': 'ir.actions.act_window',
            'name': _("%(product_name)s's homologation", product_name=self.name),

            'domain': [
                ('product_id', '=', self.id),
            ],
            'view_mode': 'tree,form',

            'context': {"create": 0},
        })

    def diff_month(self, d1, d2):
        return (d1.year - d2.year) * 12 + d1.month - d2.month

    def _compute_expired_contract(self):
        today = date.today()

        for record in self:
            record.expired_contract = True if any(
                seller.purchase_requisition_id and seller.purchase_requisition_id.date_end and
                self.diff_month(seller.purchase_requisition_id.date_end, today) <= 18 for seller in
                record.seller_ids) else False

    def _compute_expired_homologation(self):
        # Get today's date
        today = date.today()
        month_18 = today + relativedelta(months=18)

        for record in self:
            record.expired_homologation = True if any(homologation.end_date and homologation.state == 'homologue' and
                                                      self.diff_month(homologation.end_date, today) <= 18 for
                                                      homologation in record.homologation_ids) else False

    def _compute_has_blacklisted(self):
        for record in self:
            blacklist1 = True if any(
                homologation.supplier_id.is_blacklisted == True and homologation.state == 'homologue' for homologation
                in record.homologation_ids) else False
            blacklist2 = True if any(
                seller.partner_id.is_blacklisted == True for seller in
                record.seller_ids) else False
            if blacklist1 or blacklist2:
                record.has_backliested_supplier = True
            else :
                record.has_backliested_supplier = False
    # @api.depends('homologation_ids')
    def _compute_number_fournisseur(self):
        for record in self:
            record.number_fournisseur = len(record.homologation_ids.filtered(
                lambda homologation: homologation.state == 'homologue'))

    def _prepare_market_line(self):

        vals_dict = [
            (0, 0, {'product_id': self.id})]
        return vals_dict

    def _prepare_market(self):
        return {
            'company_id': self.company_id.id if self.company_id else False,
            'dw_homologate': True,
            "market_line_ids": self._prepare_market_line()
        }

    def action_launch_market(self):
        market_list = []
        DwMarket = self.env['dw.market']
        for rec in self:
            market_list.append(rec._prepare_market())
        DwMarket.create(market_list)
