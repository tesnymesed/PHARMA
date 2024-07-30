# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import random
from collections import defaultdict
from datetime import datetime
from math import log10

from odoo import api, fields, models
from odoo.tools.date_utils import add, subtract
from odoo.tools.float_utils import float_round


class DWMrpProductionSchedule(models.Model):
    _inherit = 'mrp.production.schedule'

    @api.model
    def get_mps_view_state(self, domain=False, offset=0, limit=False, start_date_range='', end_date_range=''):
        """ Return the global information about MPS and a list of production
        schedules values with the domain.

        :param domain: domain for mrp.production.schedule
        :return: values used by the client action in order to render the MPS.
            - dates: list of period name
            - date_objs: list of period Date objects
            - production_schedule_ids: list of production schedules values
            - manufacturing_period: list of periods (days, months or years)
            - company_id: user current company
            - groups: company settings that hide/display different rows
        :rtype: dict
        """

        config = super(DWMrpProductionSchedule, self).get_mps_view_state(domain=False, offset=0, limit=False)
        productions_schedules = self.env['mrp.production.schedule'].search(domain or [], offset=offset, limit=limit)
        config['date_objs'] = self.env.company._get_date_range(start_date_range=start_date_range,
                                                               end_date_range=end_date_range)
        config['dates'] = self.env.company._date_range_to_str(start_date_range=start_date_range,
                                                              end_date_range=end_date_range)
        config['production_schedule_ids'] = productions_schedules.get_production_schedule_view_state(
            start_date_range=start_date_range, end_date_range=end_date_range)

        dw_company_groups = self.env.company.read([
            'dw_mrp_mps_show_stock_wout_safety_stock',
            'dw_mrp_mps_show_stock_coverage',
        ])
        config['groups'][0].update(dw_company_groups[0])

        decision_action_ids = self.env['dw.mrp.alert.decision'].get_decision_action_items()

        config['decision_action_ids'] = decision_action_ids

        return config

    def _get_replenish_qty_wout_ss(self, after_forecast_qty):
        """ Modify the quantity to replenish depending on the min/max and targeted
        quantity for safety stock.

        param after_forecast_qty: The quantity to replenish in order to reach a
        safety stock of 0.
        return: quantity to replenish
        rtype: float
        """
        optimal_qty = 0.0 - after_forecast_qty

        if optimal_qty > self.max_to_replenish_qty:
            replenish_qty = self.max_to_replenish_qty
        elif optimal_qty <= 0:
            replenish_qty = 0
            # replenish_qty = optimal_qty
        elif optimal_qty < self.min_to_replenish_qty:
            replenish_qty = self.min_to_replenish_qty
        else:
            replenish_qty = optimal_qty

        return replenish_qty

    def get_production_schedule_view_state(self, start_date_range='', end_date_range=''):

        """ Prepare and returns the fields used by the MPS client action.
        For each schedule returns the fields on the model. And prepare the cells
        for each period depending the manufacturing period set on the company.
        The forecast cells contains the following information:

        - date_start: First day of the current period.
        - date_stop: Last day of the current period.

        - starting_inventory_qty: In the first period, the quantity available.
        In all other periods, the safety stock from previous period.

        - outgoing_qty: The outgoing moves quantity.
        - forecast_qty: Demand forecast set by the user.

        - indirect_demand_qty: On manufacturing a quantity to replenish could
        require a need for a component in another schedule.

        - incoming_qty: The incoming moves and RFQ for the specified product and
        warehouse during the current period.

        - replenish_qty: The quantity to replenish for the current period. It
        could be computed or set by the user.

        - replenish_qty_updated: True if the quantity to replenish has been set manually
        by the user.

        - safety_stock_qty: starting_inventory_qty - forecast_qty - indirect_demand_qty + replenish_qty
        """
        _use_product_lead = self.env['ir.config_parameter'].sudo().get_param('dw_mrp.dw_use_product_lead')

        company_id = self.env.company
        date_range = company_id._get_date_range(start_date_range=start_date_range, end_date_range=end_date_range)
        date_range_year_minus_1 = company_id._get_date_range(start_date_range=start_date_range,
                                                             end_date_range=end_date_range, years=1)
        date_range_year_minus_2 = company_id._get_date_range(start_date_range=start_date_range,
                                                             end_date_range=end_date_range, years=2)

        # We need to get the schedule that impact the schedules in self. Since
        # the state is not saved, it needs to recompute the quantity to
        # replenish of finished products. It will modify the indirect
        # demand and replenish_qty of schedules in self.
        schedules_to_compute = self.env['mrp.production.schedule'].browse(self.get_impacted_schedule()) | self

        # Dependencies between schedules
        indirect_demand_trees = schedules_to_compute._get_indirect_demand_tree()

        indirect_ratio_mps = schedules_to_compute._get_indirect_demand_ratio_mps(indirect_demand_trees)

        # Get the schedules that do not depends from other in first position in
        # order to compute the schedule state only once.
        indirect_demand_order = schedules_to_compute._get_indirect_demand_order(indirect_demand_trees)
        indirect_demand_qty = defaultdict(float)
        incoming_qty, incoming_qty_done = self._get_incoming_qty(date_range)
        outgoing_qty, outgoing_qty_done = self._get_outgoing_qty(date_range)
        dummy, outgoing_qty_year_minus_1 = self._get_outgoing_qty(date_range_year_minus_1)
        dummy, outgoing_qty_year_minus_2 = self._get_outgoing_qty(date_range_year_minus_2)
        read_fields = [
            'forecast_target_qty',
            'min_to_replenish_qty',
            'max_to_replenish_qty',
            'product_id',
        ]
        if self.env.user.has_group('stock.group_stock_multi_warehouses'):
            read_fields.append('warehouse_id')
        if self.env.user.has_group('uom.group_uom'):
            read_fields.append('product_uom_id')
        production_schedule_states = schedules_to_compute.read(read_fields)
        production_schedule_states_by_id = {mps['id']: mps for mps in production_schedule_states}

        for production_schedule in indirect_demand_order:
            # Bypass if the schedule is only used in order to compute indirect
            # demand.
            rounding = production_schedule.product_id.uom_id.rounding

            delays = production_schedule._get_lead_times()
            lead_time = delays['total_delay']
            # Ignore "Days to Supply Components" when set demand for components since it's normally taken care by the
            # components themselves
            lead_time_ignore_components = lead_time - production_schedule.bom_id.days_to_prepare_mo
            _lead_time = lead_time_ignore_components

            production_schedule_state = production_schedule_states_by_id[production_schedule['id']]
            if production_schedule in self:
                procurement_date = add(fields.Date.today(), days=lead_time)
                precision_digits = max(0, int(-(log10(production_schedule.product_uom_id.rounding))))
                production_schedule_state['precision_digits'] = precision_digits
                production_schedule_state['forecast_ids'] = []

            starting_inventory_qty = production_schedule.product_id.with_context(
                warehouse=production_schedule.warehouse_id.id).qty_available
            if len(date_range):
                starting_inventory_qty -= incoming_qty_done.get(
                    (date_range[0], production_schedule.product_id, production_schedule.warehouse_id), 0.0)
                starting_inventory_qty += outgoing_qty_done.get(
                    (date_range[0], production_schedule.product_id, production_schedule.warehouse_id), 0.0)

            for index, (date_start, date_stop) in enumerate(date_range):
                forecast_values = {}
                key = ((date_start, date_stop), production_schedule.product_id, production_schedule.warehouse_id)
                key_y_1 = (date_range_year_minus_1[index], *key[1:])
                key_y_2 = (date_range_year_minus_2[index], *key[1:])

                existing_forecasts = production_schedule.forecast_ids.filtered(
                    lambda p: p.date >= date_start and p.date <= date_stop)
                if production_schedule in self:
                    forecast_values['date_start'] = date_start
                    forecast_values['date_stop'] = date_stop
                    forecast_values['incoming_qty'] = float_round(
                        incoming_qty.get(key, 0.0) + incoming_qty_done.get(key, 0.0), precision_rounding=rounding)
                    forecast_values['outgoing_qty'] = float_round(
                        outgoing_qty.get(key, 0.0) + outgoing_qty_done.get(key, 0.0), precision_rounding=rounding)
                    forecast_values['outgoing_qty_year_minus_1'] = float_round(
                        outgoing_qty_year_minus_1.get(key_y_1, 0.0), precision_rounding=rounding)
                    forecast_values['outgoing_qty_year_minus_2'] = float_round(
                        outgoing_qty_year_minus_2.get(key_y_2, 0.0), precision_rounding=rounding)

                forecast_values['indirect_demand_qty'] = float_round(indirect_demand_qty.get(key, 0.0),
                                                                     precision_rounding=rounding, rounding_method='UP')
                replenish_qty_updated = False
                if existing_forecasts:
                    forecast_values['notes'] = existing_forecasts[0].notes or ''
                    forecast_values['decision'] = existing_forecasts[0].dw_alert_decision_id.id or -1
                    forecast_values['forecast_qty'] = float_round(sum(existing_forecasts.mapped('forecast_qty')),
                                                                  precision_rounding=rounding)
                    forecast_values['replenish_qty'] = float_round(sum(existing_forecasts.mapped('replenish_qty')),
                                                                   precision_rounding=rounding)

                    # Check if the to replenish quantity has been manually set or
                    # if it needs to be computed.
                    replenish_qty_updated = any(existing_forecasts.mapped('replenish_qty_updated'))
                    forecast_values['replenish_qty_updated'] = replenish_qty_updated
                else:
                    forecast_values['forecast_qty'] = 0.0
                    forecast_values['notes'] = ''
                    # forecast_values['notes'] = -1

                if not replenish_qty_updated:
                    replenish_qty = production_schedule._get_replenish_qty(
                        starting_inventory_qty - forecast_values['forecast_qty'] - forecast_values[
                            'indirect_demand_qty'])
                    forecast_values['replenish_qty'] = float_round(replenish_qty, precision_rounding=rounding)
                    forecast_values['replenish_qty_updated'] = False

                forecast_values['starting_inventory_qty'] = float_round(starting_inventory_qty,
                                                                        precision_rounding=rounding)
                forecast_values['safety_stock_qty'] = float_round(
                    starting_inventory_qty - forecast_values['forecast_qty'] - forecast_values['indirect_demand_qty'] +
                    forecast_values['replenish_qty'], precision_rounding=rounding)

                # @bislem:

                replenish_qty_wout_ss = production_schedule._get_replenish_qty_wout_ss(
                    starting_inventory_qty - forecast_values['forecast_qty'] - forecast_values['indirect_demand_qty'])
                forecast_values['replenish_qty_wout_ss'] = float_round(replenish_qty_wout_ss,
                                                                       precision_rounding=rounding)

                forecast_values['safety_stock_qty_wout_ss'] = float_round(
                    starting_inventory_qty - forecast_values['forecast_qty'] - forecast_values['indirect_demand_qty'] +
                    forecast_values['replenish_qty_wout_ss'], precision_rounding=rounding)

                if production_schedule in self:
                    production_schedule_state['forecast_ids'].append(forecast_values)
                starting_inventory_qty = forecast_values['safety_stock_qty']
                if not forecast_values['replenish_qty']:
                    continue
                # Set the indirect demand qty for children schedules.

                for (product, ratio) in indirect_ratio_mps[
                    (production_schedule.warehouse_id, production_schedule.product_id)].items():

                    if bool(_use_product_lead):
                        _security_lead_days = delays.get('security_lead_days', 0.0)
                        _product_delay = product.dw_purchase_lead
                        _lead_time = (lead_time_ignore_components
                                      - _security_lead_days
                                      + _product_delay)

                    related_date = max(
                        subtract(date_start, days=_lead_time),
                        fields.Date.today())
                    index = next(i for i, (dstart, dstop) in enumerate(date_range) if
                                 related_date <= dstart or (related_date >= dstart and related_date <= dstop))
                    related_key = (date_range[index], product, production_schedule.warehouse_id)
                    indirect_demand_qty[related_key] += ratio * forecast_values['replenish_qty']

            if production_schedule in self:
                # The state is computed after all because it needs the final
                # quantity to replenish.

                forecasts_state = production_schedule._get_forecasts_state(production_schedule_states_by_id, date_range,
                                                                           procurement_date)

                forecasts_state = forecasts_state[production_schedule.id]
                for index, forecast_state in enumerate(forecasts_state):
                    production_schedule_state['forecast_ids'][index].update(forecast_state)

                # The purpose is to hide indirect demand row if the schedule do not
                # depends from another.

                has_indirect_demand = any(
                    forecast['indirect_demand_qty'] != 0 for forecast in production_schedule_state['forecast_ids'])
                production_schedule_state['has_indirect_demand'] = has_indirect_demand
        return [p for p in production_schedule_states if p['id'] in self.ids]

    def _get_lead_times(self):
        """ Get the lead time for each product in self. The lead times are
        based on rules lead times + produce delay or supplier info delay.
        """
        rules = self.product_id._get_rules_from_location(self.warehouse_id.lot_stock_id)
        return rules._get_lead_days(self.product_id, bom=self.bom_id)[0]

    def set_notes(self, date_start, date_stop, notes):
        """ Save the forecast notes:

        params notes: The new notes
        params date_start: The manufacturing period start
        params date_start: The manufacturing period end
        """
        self.ensure_one()
        if date_start and date_stop:
            date_start = datetime.strptime(date_start, '%Y-%m-%d').date()
            date_stop = datetime.strptime(date_stop, '%Y-%m-%d').date()

        existing_forecast = self.forecast_ids.filtered(lambda f: f.date >= date_start and
                                                                 f.date <= date_stop)
        if existing_forecast:
            existing_forecast[0].write({'notes': notes})
        else:
            existing_forecast.create({
                'notes': notes,
                'date': date_stop,
                'production_schedule_id': self.id
            })
        return True

    def set_decision(self, date_start, date_stop, decision_id):
        """ Save the forecast decision:

        params decision_id: The new decision id
        params date_start: The manufacturing period start
        params date_start: The manufacturing period end
        """
        try:
            decision_id = int(decision_id)
        except ValueError as e:
            decision_id = None

        self.ensure_one()
        if date_start and date_stop:
            date_start = datetime.strptime(date_start, '%Y-%m-%d').date()
            date_stop = datetime.strptime(date_stop, '%Y-%m-%d').date()

        existing_forecast = self.forecast_ids.filtered(lambda f: f.date >= date_start and
                                                                 f.date <= date_stop)
        if existing_forecast:
            existing_forecast[0].write({'dw_alert_decision_id': decision_id})
        elif decision_id is not None:
            existing_forecast.create({
                'dw_alert_decision_id': decision_id,
                'date': date_stop,
                'production_schedule_id': self.id
            })

        return True


class DWMrpProductForecast(models.Model):
    _inherit = 'mrp.product.forecast'

    notes = fields.Text('Observations')

    dw_alert_decision_id = fields.Many2one('dw.mrp.alert.decision', string='Decision')
