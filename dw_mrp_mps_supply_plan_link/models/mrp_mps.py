# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from datetime import datetime

from odoo import api, models


class DWMrpProductionSchedule(models.Model):
    _inherit = 'mrp.production.schedule'

    @api.model
    def create_supply_plans(self, args):
        result = []
        mps_ids = [m.get('id') for m in args]

        records = self.env['mrp.production.schedule'].search([
            ('id', 'in', mps_ids),
            ('bom_id', '=', False)
        ])
        company_id = records[0].company_id.id

        comp_mps = [item for item in args if item.get('id') in records.ids]
        if comp_mps:
            dates = ((datetime.strptime(f.get('date_start'), "%Y-%m-%d").date(),
                      datetime.strptime(f.get('date_stop'), "%Y-%m-%d").date())
                     for f in comp_mps[0].get('forecast_ids', {}))

            for comp in comp_mps:
                ids = self.process_data(comp, company_id)
                if ids:
                    print(comp)
                    result.extend(ids)

            return result

    def process_data(self, input_data, company_id):
        # Group forecast_ids by year
        grouped_forecast_ids = defaultdict(list)
        ids = []
        approved_ids = []
        _forecast_ids = input_data['forecast_ids']
        for forecast_id in _forecast_ids:
            _date = datetime.strptime(forecast_id['date_start'], "%Y-%m-%d").date()
            year = _date.year

            # if year not in grouped_forecast_ids:
            #     grouped_forecast_ids[year] = []
            grouped_forecast_ids[year].append(forecast_id)

        # Create records in Model 1
        for year, forecast_ids in grouped_forecast_ids.items():
            year_s = str(year)
            existing_supply_plan = self.env['dw.mrp.supply.plan'].search([
                ('season_date', '=', year_s),
                ('company_id', '=', company_id)
            ])
            if existing_supply_plan:
                supply_plan = existing_supply_plan
            else:

                supply_plan = self.env['dw.mrp.supply.plan'].create({
                    'name': f'MPS Supply Plan Proposal {year_s}',
                    'season_date': year_s,
                    'company_id': company_id
                })

            ids.append(supply_plan.id)

            # Create records in Model 2
            product_id = input_data['product_id'][0]
            product_uom_id = input_data['product_uom_id'][0]

            ex_supply_plan_line = self.env['dw.mrp.supply.plan.lines'].search([
                ('supply_plan_id', '=', supply_plan.id),
                ('product_id', '=', product_id),
                # ('uom_id', '=', product_uom_id),
            ])

            if ex_supply_plan_line:
                supply_plan_line = ex_supply_plan_line
            else:
                supply_plan_line = self.env['dw.mrp.supply.plan.lines'].create({
                    'product_id': product_id,
                    'uom_id': product_uom_id,
                    'supply_plan_id': supply_plan.id,
                })

            # Create records in Model 3
            # for year, forecast_ids in grouped_forecast_ids.items():
            for forecast_id in forecast_ids:
                _date = datetime.strptime(forecast_id['date_start'], "%Y-%m-%d").date()
                # Search for existing records
                existing_records = self.env['dw.mrp.product.supply.plan'].search([
                    ('date', '=', _date),
                    # ('supply_plan_id', '=', supply_plan.id),
                    ('product_supply_plan_id', '=', supply_plan_line.id),
                ])

                if existing_records:

                    approved = existing_records[0].filtered(lambda l: l.state != 'draft')
                    if approved:
                        approved_ids.append(approved.id)
                        continue
                    # Update existing records
                    existing_records[0].write({
                        'quantity_planned': forecast_id.get('indirect_demand_qty'),
                        # 'quantity_approved': forecast_id['replenish_qty'],
                        # 'quantity_done': 0,
                        # 'quantity_to_order': forecast_id['replenish_qty_wout_ss'],
                    })
                else:
                    # Create a new record
                    self.env['dw.mrp.product.supply.plan'].create({
                        'date': _date,
                        'date_launch': _date,
                        'quantity_planned': forecast_id.get('indirect_demand_qty'),
                        # 'quantity_approved': forecast_id['replenish_qty'],
                        # 'quantity_done': 0,
                        # 'quantity_to_order': forecast_id['replenish_qty_wout_ss'],
                        'product_supply_plan_id': supply_plan_line.id,
                    })

        return ids, approved_ids

    def action_open_supply_plans(self, supply_plan_ids):
        """
        """
        self.ensure_one()

        return {
            'name': 'MRP Supply Plans',
            'type': 'ir.actions.act_window',
            'res_model': 'dw.mrp.supply.plan',
            'views': [(False, 'tree'), (False, 'form')],
            'view_mode': 'tree,form',
            'target': 'current',
            # 'domain': [('id', 'in', supply_plan_ids)],
        }
