# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, date

from odoo import api, models

__SEPARATOR__ = '- V'


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

            _forecast_ids = comp_mps[0].get('forecast_ids')

            date_start = min(datetime.strptime(i.get('date_start'), "%Y-%m-%d").date() for i in _forecast_ids)
            date_end = max(datetime.strptime(i.get('date_stop'), "%Y-%m-%d").date() for i in _forecast_ids)

            _dseq = date.today().strftime('%m%y')
            company_name = records[0].company_id.name

            # Create records in Model 1
            # Base name format
            base_name = f'PAPPRO/M-{_dseq}-{company_name}{__SEPARATOR__}'
            # Check existing names to determine the next version number
            existing_supply_plans = self.env['dw.mrp.supply.plan'].search([
                ('name', 'ilike', f'{base_name}%'),
                ('company_id', '=', company_id),  # Ensure we are checking within the same company
                ('start_date', '=', date_start),
                ('end_date', '=', date_end)
            ])

            # Determine the next version number
            if existing_supply_plans:
                versions = [int(plan.name.split(__SEPARATOR__)[-1]) for plan in existing_supply_plans if
                            plan.name.split(__SEPARATOR__)[-1].isdigit()]
                next_version = max(versions) + 1
            else:
                next_version = 1

            # Create the full name with versioning
            full_name = f'{base_name}{next_version:02d}'  # Formats the version number as two digits (e.g., V01, V02)

            # Create the supply plan
            supply_plan = self.env['dw.mrp.supply.plan'].create({
                'name': full_name,
                'start_date': date_start,
                'end_date': date_end,
                'company_id': company_id
            })

            # Create records in Model 2 & 3

            for comp in comp_mps:
                ids = self.process_data(comp, supply_plan)
                if ids:
                    result.extend(ids)

        return result

    def process_data(self, input_data, supply_plan):
        ids = []

        _forecast_ids = input_data['forecast_ids']

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
        for forecast_id in _forecast_ids:
            _date = datetime.strptime(forecast_id['date_start'], "%Y-%m-%d").date()
            # Search for existing records
            existing_records = self.env['dw.mrp.product.supply.plan'].search([
                ('date', '=', _date),
                # ('supply_plan_id', '=', supply_plan.id),
                ('product_supply_plan_id', '=', supply_plan_line.id)
            ])

            record_vals = {'quantity_planned': forecast_id.get('indirect_demand_qty')}

            if forecast_id.get('notes'):
                record_vals['dw_mps_forecast_notes'] = forecast_id.get('notes')

            if forecast_id.get('decision', -1) != -1:
                record_vals['dw_mps_forecast_decision_id'] = forecast_id.get('decision')

            if existing_records:
                # Update existing records
                existing_records[0].write(record_vals)
                id = existing_records.id

            else:
                # Create a new record
                record_vals.update({
                    'date': _date,
                    'date_launch': _date,
                    'product_supply_plan_id': supply_plan_line.id
                })

                id = self.env['dw.mrp.product.supply.plan'].create(record_vals)

            ids.append(id)

        return ids


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
