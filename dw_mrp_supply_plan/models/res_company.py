# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models

from .utils import _PFX_PRODUCT_SUPPLY_PLAN, _PFX_SUPPLY_PLAN_LINE


class Company(models.Model):
    _inherit = "res.company"
    _check_company_auto = True

    def _create_dw_mrp_supply_plan_lines_sequence(self):
        dw_spl_vals = []
        for company in self:
            _comp_n = company.name
            dw_spl_vals.append({
                'name': f'{_comp_n} Sequence DW MRP Supply Plan Lines',
                'code': 'dw.mrp.supply.plan.lines',
                'company_id': company.id,
                'prefix': f'{_comp_n}/{_PFX_SUPPLY_PLAN_LINE}/',
                'padding': 5,
                'number_next': 1,
                'number_increment': 1
            })
        if dw_spl_vals:
            self.env['ir.sequence'].create(dw_spl_vals)

    def _create_dw_mrp_product_supply_plan_lines_sequence(self):
        dw_prdct_spl_vals = []
        for company in self:
            _comp_n = company.name
            dw_prdct_spl_vals.append({
                'name': f'{_comp_n} Sequence DW MRP Product Supply Plan',
                'code': 'dw.mrp.product.supply.plan',
                'company_id': company.id,
                'prefix': f'{_comp_n}/{_PFX_PRODUCT_SUPPLY_PLAN}/',
                'padding': 5,
                'number_next': 1,
                'number_increment': 1
            })
        if dw_prdct_spl_vals:
            self.env['ir.sequence'].create(dw_prdct_spl_vals)

    def _create_per_company_sequences(self):
        self.ensure_one()
        super()._create_per_company_sequences()
        self._create_dw_mrp_supply_plan_lines_sequence()
        self._create_dw_mrp_product_supply_plan_lines_sequence()

    @api.model_create_multi
    def create(self, vals_list):
        companies = super().create(vals_list)

        for company in companies:
            company.sudo()._create_per_company_sequences()

        return companies

    @api.model
    def create_missing_supply_plan_sequence(self):
        company_ids = self.env['res.company'].search([])
        company_has_spl_seq = self.env['ir.sequence'].search([('code', '=', 'dw.mrp.supply.plan.lines')]).mapped(
            'company_id')
        company_todo_sequence = company_ids - company_has_spl_seq

        company_todo_sequence._create_dw_mrp_supply_plan_lines_sequence()

    @api.model
    def create_missing_product_supply_plan_sequence(self):
        company_ids = self.env['res.company'].search([])
        company_has_spl_seq = self.env['ir.sequence'].search([('code', '=', 'dw.mrp.product.supply.plan')]).mapped(
            'company_id')
        company_todo_sequence = company_ids - company_has_spl_seq

        company_todo_sequence._create_dw_mrp_product_supply_plan_lines_sequence()
