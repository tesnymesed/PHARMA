# -*- coding: utf-8 -*-

import datetime
from collections import OrderedDict, defaultdict, namedtuple
from itertools import groupby
from math import log10

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.osv.expression import OR, AND
from odoo.tools.date_utils import add
from odoo.tools.float_utils import float_round

from .utils import calculate_planned_production_qty, round_up_to_nearest, safe_divide


class DwProductionPlanSimulator(models.Model):
    _name = 'dw.production.plan.simulation'
    _order = 'company_id, sequence'
    _description = 'Simulate the production of Product'

    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    product_id = fields.Many2one('product.product', required=True,
                                 # domain=[('product_tmpl_id.categ_id.is_final_product', '=', True),
                                 #         ('product_tmpl_id.bom_ids', '!=', False)],
                                 # domain=['|', ('product_tmpl_id.company_id', '=', company_id), ('product_tmpl_id.company_id', '=', False)],
                                 domain=[
                                     ('product_tmpl_id.categ_id.is_final_product', '=', True),
                                     # ('product_tmpl_id.bom_ids', '!=', False),
                                     '|',
                                     ('product_tmpl_id.company_id', '=', company_id),
                                     ('product_tmpl_id.company_id', '=', False)
                                 ]
                                 )

    product_tmpl_id = fields.Many2one('product.template',
                                      related="product_id.product_tmpl_id",
                                      store=True, readonly=True)
    # product_category_id = fields.Many2one('product.category', related="product_tmpl_id.categ_id",
    #                                       readonly=True,  store=True)
    product_uom_id = fields.Many2one('uom.uom', string='Product UoM',
                                     related='product_id.uom_id', store=True
                                     )
    sequence = fields.Integer(related='product_id.sequence', store=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Production Warehouse', store=True,
                                   default=lambda self: self._default_warehouse_id())
    bom_id = fields.Many2one(
        'mrp.bom', "Bill of Materials", store=True,
        domain="[('product_tmpl_id', '=', product_tmpl_id), '|', ('product_id', '=', product_id), ('product_id', '=', False)]",
        # domain="['|', ('product_id', '=', product_id), ('product_id', '=', False)]",
        # check_company=True
    )

    lot_size = fields.Float(
        related='bom_id.product_qty',
        compute='_compute_lot_size',
        readonly=False,
        store=True
    )

    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center',
                                    # domain="[('dw_simulation_ok', '=', True)]",
                                    context={"dw_pharma_simulation": True, "dw_bypass_pharma_simulation": False},
                                    default=lambda self: self._default_workcenter_id(), store=True)

    workcenter_default_capacity = fields.Float('Capacity', default=1.0,
                                               related="workcenter_id.default_capacity",
                                               readonly=False,
                                               store=True,
                                               help="Default number of pieces (in product UoM) that can be produced in parallel (at the same time) at this work center.")

    product_plan_sim_ids = fields.One2many('dw.product.production.plan.simulation', 'production_simulation_id',
                                           'Simulation quantity at date')

    safety_stock_target_qty = fields.Float(
        'Safety Stock Target Qty (Months worth)',
        compute='_compute_safety_stock_target_qty',
        help="This is the minimum free stock you want to keep for that product at all times.")

    safety_stock_target = fields.Integer(
        'Safety Stock Target (Months)',
        default=4,
        help="This is the minimum free stock you want to keep for that product at all times (Months worth of sales).")

    sales_average = fields.Float(compute='compute_sales_average', default=0.0, store=True)

    min_to_replenish_qty = fields.Float(
        'Minimum to Replenish',
        help="Unless the demand is 0, Odoo will always at least replenish this quantity.")
    max_to_replenish_qty = fields.Float(
        'Maximum to Replenish', default=1000,
        help="The maximum replenishment you would like to launch for each period in the MPS. Note that if the demand is higher than that amount, the remaining quantity will be transferred to the next period automatically.")

    # @bislem: [ADD] Nov 2nd, 2024
    simulation_version_id = fields.Many2one('dw.production.plan.simulation.version',
                                            string='Production Plan Simulation Version',
                                            help="Reference to the simulation version.")

    # replenish_state = fields.Selection([
    #     ('to_replenish', 'To Replenish'),
    #     ('under_replenishment', 'Under Replenishment'),
    #     ('excessive_replenishment', 'Excessive Replenishment')], store=False, search='_search_replenish_state',
    #     help="Technical field to support filtering by replenish state")
    #
    # _sql_constraints = [
    #     ('warehouse_product_ref_uniq', 'unique (warehouse_id, product_id)', 'The combination of warehouse and product must be unique!'),
    # ]
    def apply_search_filter(self):
        pass

    def dw_action_open_mps_view(self, state):
        # self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("dw_production_plan_simulator.action_dw_mrp_mps")
        # action['context'] = {'dw_pharma_simulation': True, 'dw_bypass_pharma_simulation': False}

        # action['domain'] = [('dw_simulation_ok', '=', 'true')]
        # product_ids = [l[0].product_id.id for l in bom_lines]
        # product_ids_with_forecast = self.env['mrp.production.schedule'].search([
        #     ('company_id', '=', production_schedule.company_id.id),
        #     ('warehouse_id', '=', production_schedule.warehouse_id.id),
        #     ('product_id', 'in', product_ids)
        # ]).product_id.ids
        _domain = state.get('domain')

        if _domain and not action.get('domain'):
            print('_domain', _domain)
            action['domain'] = _domain
            print(action, action.get('domain'))

        return action

        # {
        #   name: "DW Materials Availability",
        #   type: "ir.actions.client",
        #   tag: "dw_mrp_mps_client_action",
        #   target: "current",
        #   domain: [["company_id", "=", state.currentCompanyId]],
        #   params: {
        #     company: state.currentCompanyId,
        #     startDate: state.startDate,
        #     endDate: state.endDate,
        #     dw_bypass_pharma_simulation: false,
        #     dw_pharma_simulation: true,
        #   },
        #   context: {
        #     company: state.currentCompanyId,
        #     startDate: state.startDate,
        #     endDate: state.endDate,
        #     dw_bypass_pharma_simulation: false,
        #     dw_pharma_simulation: true,
        #   },
        #
        #   //          views: [[false, "form"]],
        #   //          res_model: "dw.production.plan.simulation",
        #   //          res_id: productionSimulationId,
        # }

    @api.depends('company_id.dw_prod_sim_date_sales_range_start',
                 'company_id.dw_prod_sim_date_sales_range_end',
                 'product_plan_sim_ids.sold_qty',
                 'safety_stock_target')
    def compute_sales_average(self):
        for record in self:
            found_in_range = False

            print(record)
            start = record.company_id.dw_prod_sim_date_sales_range_start
            end = record.company_id.dw_prod_sim_date_sales_range_end
            d = relativedelta(end, start)
            m_count = d.months
            if d.days > 0:
                m_count += 1

            existing_prdct_sim_ids = record.product_plan_sim_ids.filtered(lambda p: start <= p.date <= end)
            if existing_prdct_sim_ids:
                sales = existing_prdct_sim_ids.mapped('sold_qty')
                found_in_range = True
            else:
                sales = record.product_plan_sim_ids.mapped('sold_qty')

            sales_avg = safe_divide(sum(sales), m_count)
            record.sales_average = sales_avg

        return True

    def calculate_sales_average(self, company_id, start_date=None, end_date=None):
        for record in self:
            print(record)
            qr = self._query(record.product_id.id)
            sales = self._sales_query(qr)

            record.sales_average = self.calculate_average_qty_to_deliver(sales)

    @api.depends('safety_stock_target', 'sales_average')
    def _compute_safety_stock_target_qty(self):
        for record in self:
            record.safety_stock_target_qty = record.safety_stock_target * record.sales_average

    @api.model
    def _default_warehouse_id(self):
        return self.env['stock.warehouse'].search(self.env['stock.warehouse']._check_company_domain(self.env.company),
                                                  limit=1)

    @api.model
    def _default_workcenter_id(self):
        return self.env['mrp.workcenter'].with_context(dw_pharma_simulation=True).search(
            self.env['mrp.workcenter']._check_company_domain(self.env.company),
            limit=1)

    @api.depends('bom_id')
    def _compute_lot_size(self):
        for record in self:
            record.lot_size = record.bom_id.product_qty

    @api.model
    def get_prod_simulator_view_state(self, domain=False, offset=0, limit=False, start_date='', end_date=''):
        """ Return the global information about MPS and a list of production
        schedules values with the domain.

        :param domain: domain for dw.production.plan.simulation
        :return: values used by the client action in order to render the MPS.
            - dates: list of period name
            - production_simulation_ids: list of production schedules values
            - manufacturing_period: list of periods (days, months or years)
            - company_id: user current company
            - groups: company settings that hide/display different rows
        :rtype: dict
        """
        production_simulations = self.env['dw.production.plan.simulation'].search(domain or [], offset=offset,
                                                                                  limit=limit)
        count = self.env['dw.production.plan.simulation'].search_count(domain or [])
        production_simulations_states = production_simulations.get_production_simulation_view_state(
            start_date_range=start_date, end_date_range=end_date)

        workcenter_capacities = self.get_workcenter_capacities(production_simulations_states)
        company_groups = self.env.company.read([
            'mrp_mps_show_starting_inventory',
            'mrp_mps_show_demand_forecast',
            'mrp_mps_show_indirect_demand',
            'mrp_mps_show_actual_demand',
            'mrp_mps_show_to_replenish',
            'mrp_mps_show_actual_replenishment',
            'mrp_mps_show_safety_stock',
            'mrp_mps_show_available_to_promise',
            'mrp_mps_show_actual_demand_year_minus_1',
            'mrp_mps_show_actual_demand_year_minus_2',
        ])

        decision_action_ids = self.env['dw.mrp.alert.decision'].get_decision_action_items()

        return {
            'dates': self.env.company._date_range_to_str(start_date_range=start_date,
                                                         end_date_range=end_date),
            # 'production_simulation_ids': proxy.get('production_simulation_ids'),
            'production_simulation_ids': production_simulations_states,
            'workcenter_capacities': workcenter_capacities,
            'decision_action_ids': decision_action_ids,
            'company_id': self.env.company.id,
            'groups': company_groups,
            'count': count,
        }

    def get_workcenter_capacities(self, production_simulations):

        def key_func(k):
            return k['date_start']

        results = []

        # Process each record in the data
        company_id = self.company_id or self.env.company
        date_range = company_id._get_simulation_date_range()
        # Group the product_plan_sim_ids by date_start and date_stop
        grouped_simulations = groupby(production_simulations, key=lambda r: r["workcenter_id"])

        for workcenter, group in grouped_simulations:

            if workcenter:
                l_group = list(group)
                l_merged = []
                for prdct_i in l_group:
                    product_plan_sim_ids = prdct_i.get('product_plan_sim_ids')
                    for plan_sim_i in product_plan_sim_ids:
                        plan_sim_i.update({'id': prdct_i.get('id')})

                    l_merged.extend(product_plan_sim_ids)

                # Group by date_start and sum
                res = []
                # for (date_start, date_stop), grp in groupby(l_merged, key=lambda r: (r["date_start"], r["date_stop"])):
                for index, (date_start, date_stop) in enumerate(date_range):

                    group_data = [i for i in l_merged if (isinstance(i['date_start'], str) and
                                                          datetime.datetime.strptime(i['date_start'],
                                                                                     '%Y-%m-%d').date() == date_start)
                                  or (isinstance(i['date_start'], datetime.date) and i['date_start'] == date_start)]

                    if group_data:
                        total_required_capacity = sum(item["required_capacity"] for item in group_data)
                        total_production_objective_qty = sum(item["production_objective_qty"] for item in group_data)
                        # Sample list of strings
                        # notes_str = "\n".join([item.get("notes") for item in group_data if item.get("notes")])
                        notes_str = group_data[0].get("alert_notes")
                        decision = group_data[0].get("decision")

                        if total_required_capacity < total_production_objective_qty:
                            pass

                        total_capacity_utilisation = sum(item["capacity_utilisation"] for item in group_data)

                        if total_capacity_utilisation >= 90:
                            _year = date_start.year
                            _quarter = (date_start.month - 1) // 3 + 1
                            _q_y_f = f"Q{_quarter} {_year}"

                            res.append({
                                "id": [i.get('id') for i in group_data],
                                "workcenter": workcenter,
                                "workcenter_name": workcenter[1],
                                "date_start": date_start,
                                "date_stop": date_stop,
                                "year": _year,
                                "quarter": _q_y_f,
                                "capacity_utilisation": total_capacity_utilisation,
                                "required_capacity": total_required_capacity,
                                "production_objective_qty": total_production_objective_qty,
                                "alert_notes": notes_str,
                                "decision": decision
                            })

                    else:
                        continue
                results.extend(res)
            else:
                continue

        return results

        # # Group the product_plan_sim_ids by date_start and date_stop
        # grouped_simulators = groupby(group["product_plan_sim_ids"],
        #                              key=lambda r: (r["date_start"], r["date_stop"]))

        #     # Initialize a dictionary to store the required capacity sum for each date range
        #     capacity_sums = {}
        #
        #     # Iterate over the groups and calculate the sum of required capacity for each date range
        #     for (date_start, date_stop), group in grouped_simulators:
        #         required_capacity_sum = sum(plan_sim["required_capacity"] for plan_sim in group)
        #         capacity_sums[(date_start, date_stop)] = capacity_sums.get((date_start, date_stop),
        #                                                                    0) + required_capacity_sum
        #
        #     # Add the required capacity sums to the corresponding workcenter
        #     if workcenter_id in grouped_data:
        #         grouped_data[workcenter_id].update(capacity_sums)
        #     else:
        #         grouped_data[workcenter_id] = capacity_sums
        # for production_simulation in production_simulations:
        #     pass

    def _search_replenish_state(self, operator, value):
        production_simulations = self.search([])
        production_simulations_states = production_simulations.get_production_simulation_view_state()

        def filter_function(f):
            if not value:
                return not (f['state'] == 'to_launch' and f['to_replenish'] or \
                            f['state'] == 'to_relaunch' or f['state'] == 'to_correct')
            return value == "to_replenish" and f['state'] == 'to_launch' and f['to_replenish'] or \
                value == "under_replenishment" and f['state'] == 'to_relaunch' or \
                value == "excessive_replenishment" and f['state'] == 'to_correct'

        ids = []
        for state in production_simulations_states:
            if value:
                if any(map(filter_function, state['product_plan_sim_ids'])):
                    ids.append(state['id'])
            else:
                if all(map(filter_function, state['product_plan_sim_ids'])):
                    ids.append(state['id'])

        if operator == '=':
            operator = 'in'
        else:
            operator = 'not in'

        return [('id', operator, ids)]

    # TODO: get From
    def action_open_actual_demand_details(self, date_str, date_start_str, date_stop_str):
        """ Open the picking list view for the actual demand for the current
        schedule.

        :param date_str: period name for the simulation sellected
        :param date_start: select incoming moves after this date
        :param date_stop: select incoming moves before this date
        :return: action values that open the picking list
        :rtype: dict
        """
        self.ensure_one()
        date_start = fields.Date.from_string(date_start_str)
        date_stop = fields.Date.from_string(date_stop_str)
        domain_moves = self._get_moves_domain(date_start, date_stop, 'outgoing')
        moves_by_date = self._get_moves_and_date(domain_moves)
        picking_ids = self._filter_moves(moves_by_date, date_start, date_stop).mapped('picking_id').ids
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'views': [(False, 'list'), (False, 'form')],
            'view_mode': 'list,form',
            'name': _('Actual Demand %s %s (%s - %s)', self.product_id.display_name, date_str, date_start_str,
                      date_stop_str),
            'target': 'current',
            'domain': [('id', 'in', picking_ids)],
        }

    def action_open_actual_replenishment_details(self, date_str, date_start_str, date_stop_str):
        """ Open the actual replenishment details.

        :param date_str: period name for the simulation sellected
        :param date_start: select incoming moves and RFQ after this date
        :param date_stop: select incoming moves and RFQ before this date
        :return: action values that open the simulation details wizard
        :rtype: dict
        """
        date_start = fields.Date.from_string(date_start_str)
        date_stop = fields.Date.from_string(date_stop_str)
        domain_moves = self._get_moves_domain(date_start, date_stop, 'incoming')
        moves_by_date = self._get_moves_and_date(domain_moves)
        move_ids = self._filter_moves(moves_by_date, date_start, date_stop).ids

        rfq_domain = self._get_rfq_domain(date_start, date_stop)
        purchase_order_by_date = self._get_rfq_and_planned_date(rfq_domain)
        purchase_order_line_ids = self._filter_rfq(purchase_order_by_date, date_start, date_stop).ids
        name = _('Actual Replenishment %s %s (%s - %s)', self.product_id.display_name, date_str, date_start_str,
                 date_stop_str)

        context = {
            'default_move_ids': move_ids,
            'default_purchase_order_line_ids': purchase_order_line_ids,
            'action_name': name,
        }
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'view_mode': 'form',
            'res_model': 'mrp.mps.simulation.details',
            'views': [(False, 'form')],
            'target': 'new',
            'context': context
        }

    def action_replenish(self, based_on_lead_time=False):
        """ Run the procurement for production schedule in self. Once the
        procurements are launched, mark the simulation as launched (only used
        for state 'to_relaunch')

        :param based_on_lead_time: 2 replenishment options exists in MPS.
        based_on_lead_time means that the procurement for self will be launched
        based on lead times.
        e.g. period are daily and the product have a manufacturing period
        of 5 days, then it will try to run the procurements for the 5 first
        period of the schedule.
        If based_on_lead_time is False then it will run the procurement for the
        first period that need a replenishment
        """
        production_simulation_states = self.get_production_simulation_view_state()
        production_simulation_states = {mps['id']: mps for mps in production_simulation_states}
        procurements = []
        forecasts_values = []
        forecasts_to_set_as_launched = self.env['dw.product.production.plan.simulation']
        for production_simulation in self:
            production_simulation_state = production_simulation_states[production_simulation.id]
            # Check for kit. If a kit and its component are both in the MPS we want to skip the
            # the kit procurement but instead only refill the components not in MPS
            bom = self.env['mrp.bom']._bom_find(
                production_simulation.product_id,
                company_id=production_simulation.company_id.id,
                bom_type='phantom')[production_simulation.product_id]
            product_ratio = []
            if bom:
                dummy, bom_lines = bom.explode(production_simulation.product_id, 1)
                product_ids = [l[0].product_id.id for l in bom_lines]
                product_ids_with_forecast = self.env['dw.production.plan.simulation'].search([
                    ('company_id', '=', production_simulation.company_id.id),
                    ('warehouse_id', '=', production_simulation.warehouse_id.id),
                    ('product_id', 'in', product_ids)
                ]).product_id.ids
                product_ratio += [
                    (l[0], l[0].product_qty * l[1]['qty'])
                    for l in bom_lines if l[0].product_id.id not in product_ids_with_forecast
                ]

            # Cells with values 'to_replenish' means that they are based on
            # lead times. There is at maximum one simulation by schedule with
            # 'forced_replenish', it's the cell that need a modification with
            #  the smallest start date.
            replenishment_field = based_on_lead_time and 'to_replenish' or 'forced_replenish'
            forecasts_to_replenish = filter(lambda f: f[replenishment_field],
                                            production_simulation_state['product_plan_sim_ids'])
            for simulation in forecasts_to_replenish:
                existing_forecasts = production_simulation.product_plan_sim_ids.filtered(
                    lambda p: p.date >= simulation['date_start'] and p.date <= simulation['date_stop'])

                extra_values = production_simulation._get_procurement_extra_values(simulation)
                quantity = simulation['replenish_qty'] - simulation['incoming_qty']
                if not bom:
                    procurements.append(self.env['procurement.group'].Procurement(
                        production_simulation.product_id,
                        quantity,
                        production_simulation.product_uom_id,
                        production_simulation.warehouse_id.lot_stock_id,
                        production_simulation.product_id.name,
                        'MPS', production_simulation.company_id, extra_values
                    ))
                else:
                    for bom_line, qty_ratio in product_ratio:
                        procurements.append(self.env['procurement.group'].Procurement(
                            bom_line.product_id,
                            quantity * qty_ratio,
                            bom_line.product_uom_id,
                            production_simulation.warehouse_id.lot_stock_id,
                            bom_line.product_id.name,
                            'MPS', production_simulation.company_id, extra_values
                        ))

                if existing_forecasts:
                    forecasts_to_set_as_launched |= existing_forecasts
                else:
                    forecasts_values.append({
                        'forecasted_demand_qty': 0,
                        'date': simulation['date_stop'],
                        # 'procurement_launched': True,
                        'production_simulation_id': production_simulation.id
                    })
        if procurements:
            self.env['procurement.group'].with_context(skip_lead_time=True).run(procurements)

        # forecasts_to_set_as_launched.write({
        #     'procurement_launched': True,
        # })
        if forecasts_values:
            self.env['dw.product.production.plan.simulation'].create(forecasts_values)

    def _get_warehouse_id(self, company_id):
        return self.env['stock.warehouse'].search([('company_id', '=', company_id)], limit=1)

    @api.model
    def create_product_simulations(self, company_id):
        # Create the simulation records
        ids = []
        existing_pps = []

        # Get the final products with BOMs for the given company
        products_list = self.env['product.product'].search([
            ('product_tmpl_id.type', '=', 'product'),
            ('product_tmpl_id.categ_id.is_final_product', '=', True),
            ('product_tmpl_id.company_id', '=', company_id),
        ])

        for product in products_list:
            # Check for existing simulation records
            pps = self.env['dw.production.plan.simulation'].search([
                ('company_id', '=', company_id),
                ('product_id', '=', product.id),
                # Check for BOM
                ('bom_id', '=', product.product_tmpl_id.bom_ids[0].id) if product.product_tmpl_id.bom_ids
                else ('bom_id', '=', False)
            ], limit=1)

            if pps:
                # If we found an existing simulation, store it
                existing_pps.append(pps.id)
                continue  # Skip to the next product if a match is found

            # Prepare values for the new simulation record
            vals = {
                'company_id': company_id,
                'product_id': product.id,
                'warehouse_id': self._get_warehouse_id(company_id).id,
            }

            if product.product_tmpl_id.bom_ids:
                vals['bom_id'] = product.product_tmpl_id.bom_ids[0].id
                vals['lot_size'] = product.product_tmpl_id.bom_ids[0].product_qty

            # Create new simulation record
            pps = self.env['dw.production.plan.simulation'].create([vals])
            existing_pps.append(pps.id)  # Store the newly created simulation

        # After processing all products, handle simulation_version_id logic
        if existing_pps:
            # Check existing records for simulation_version_id
            existing_versions = self.env['dw.production.plan.simulation'].search([
                ('id', 'in', existing_pps)
            ]).mapped('simulation_version_id')

            if not any(existing_versions):  # If none have a version
                # Create a new version and link all records
                new_version = self.env['dw.production.plan.simulation.version'].create({
                    'name': self.env['dw.production.plan.simulation.version'].format_name(company_id),
                    'company_id': company_id,
                    # Add other necessary fields for the version
                })
                for existing_pp_id in existing_pps:
                    existing_pp = self.env['dw.production.plan.simulation'].browse(existing_pp_id)
                    existing_pp.simulation_version_id = new_version.id
            else:
                # If some have a version, check if they are all the same
                unique_versions = set(existing_versions)
                if len(unique_versions) > 1:
                    # If they are not all the same, link those without a version to the existing version
                    for existing_pp_id in existing_pps:
                        existing_pp = self.env['dw.production.plan.simulation'].browse(existing_pp_id)
                        if not existing_pp.simulation_version_id:
                            # Link to the first version found
                            existing_pp.simulation_version_id = existing_versions[0]
                # If all have the same version, do nothing

        return ids

    @api.model
    def create_mps_from_plan_simulations(self, company_id, production_simulations):
        ids = []
        for prod_sim in production_simulations:
            vals = {
                'product_id': prod_sim.get('product_id')[0],
                'company_id': company_id,
            }

            _id = prod_sim.get('id')

            pps = self.search([('id', '=', _id)], limit=1)

            if pps:
                vals['bom_id'] = pps.bom_id.id if pps.bom_id else False
                vals['warehouse_id'] = pps.warehouse_id.id

            # mps = self.env['mrp.production.schedule'].with_context(dw_pharma_simulation=True).create([vals])
            mps = self.env['mrp.production.schedule'].create([vals])
            mps.write({
                'forecast_target_qty': prod_sim.get('safety_stock_target_qty'),
                'min_to_replenish_qty': pps.lot_size,
                'max_to_replenish_qty': 1000 * pps.lot_size,
            })

            product_plan_sim_ids = prod_sim.get('product_plan_sim_ids')
            for prdct_sim_i in product_plan_sim_ids:
                date_start = datetime.datetime.strptime(prdct_sim_i.get('date_start'), "%Y-%m-%d").date()
                date_stop = datetime.datetime.strptime(prdct_sim_i.get('date_stop'), "%Y-%m-%d").date()

                existing_forecast = mps.forecast_ids.filtered(lambda f: date_start <= f.date <= date_stop)
                _qty = float_round(prdct_sim_i.get('suggested_production_plan_qty'),
                                   precision_rounding=mps.product_uom_id.rounding)

                forecast_vals = {
                    'forecast_qty': _qty
                }

                # Production plan Changes
                if prdct_sim_i.get('notes'):
                    forecast_vals['dw_pps_production_notes'] = prdct_sim_i.get('notes')

                # Capacity constraints
                if prdct_sim_i.get('alert_notes'):
                    forecast_vals['dw_pps_capacity_notes'] = prdct_sim_i.get('alert_notes')

                if prdct_sim_i.get('decision', -1) != -1:
                    forecast_vals['dw_pps_capacity_decision_id'] = prdct_sim_i.get('decision')

                if existing_forecast:
                    existing_forecast[0].write(forecast_vals)
                else:
                    forecast_vals['production_schedule_id'] = mps.id
                    forecast_vals['date'] = date_stop

                    self.env['mrp.product.forecast'].create(forecast_vals)

            ids.append(mps.id)

        return ids
        # # Get the final products with BOMs for the given company
        # products = self.env['product.product'].search([
        #     ('product_tmpl_id.type', '=', 'product'),
        #     ('product_tmpl_id.categ_id.is_final_product', '=', True),
        #     # ('product_tmpl_id.bom_ids', '!=', False),
        #     ('product_tmpl_id.company_id', '=', company_id)
        # ])

        # # Create the simulation records
        # ids = []
        # for product in products:
        #     _id = self.env['dw.production.plan.simulation'].create({
        #         'company_id': company_id,
        #         'product_id': product.id,
        #         'warehouse_id': self._get_warehouse_id(company_id).id,
        #         'bom_id': product.product_tmpl_id.bom_ids[0].id,
        #         'lot_size': product.product_tmpl_id.bom_ids[0].product_qty
        #     })
        #     ids.append(_id)

        # return ids

    @api.model_create_multi
    def create(self, vals_list):
        """ If the BoM is pass at the creation, create MPS for its components """
        existing_mps = []
        for i, vals in enumerate(vals_list):
            if vals.get('bom_id'):
                mps = self.search([
                    ('product_id', '=', vals.get('product_id')),
                    # ('bom_id', '=', vals.get('bom_id')),
                    ('warehouse_id', '=', vals.get('warehouse_id', self._default_warehouse_id().id)),
                    ('company_id', '=', vals.get('company_id', self.env.company.id)),
                ], limit=1)
                if mps:
                    mps.bom_id = vals.get('bom_id')
                    existing_mps.append((i, mps.id))

        for i_remove, __ in reversed(existing_mps):
            del vals_list[i_remove]

        mps = super().create(vals_list)

        mps_ids = mps.ids
        for i, mps_id in existing_mps:
            mps_ids.insert(i, mps_id)
        mps = self.browse(mps_ids)

        return mps

    def get_production_simulation_view_state(self, start_date_range='', end_date_range=''):
        """ Prepare and returns the fields used by the MPS client action.
        For each schedule returns the fields on the model. And prepare the cells
        for each period depending the manufacturing period set on the company.
        The simulation cells contains the following information:
        - forecasted_demand_qty: Demand simulation set by the user
        - date_start: First day of the current period
        - date_stop: Last day of the current period
        - replenish_qty: The quantity to replenish for the current period. It
        could be computed or set by the user.
        - replenish_qty_updated: The quantity to replenish has been set manually
        by the user.
        - starting_inventory_qty: During the first period, the quantity
        available. After, the safety stock from previous period.
        - incoming_qty: The incoming moves and RFQ for the specified product and
        warehouse during the current period.
        - outgoing_qty: The outgoing moves quantity.
        - indirect_demand_qty: On manufacturing a quantity to replenish could
        require a need for a component in another schedule. e.g. 2 product A in
        order to create 1 product B. If the replenish quantity for product B is
        10, it will need 20 product A.
        - safety_stock_qty:
        starting_inventory_qty - forecasted_demand_qty - indirect_demand_qty + replenish_qty
        """
        company_id = self.company_id or self.env.company
        date_range = company_id._get_simulation_date_range()
        date_range_year_minus_1 = company_id._get_simulation_date_range(years=1)
        date_range_year_minus_2 = company_id._get_simulation_date_range(years=2)

        # We need to get the schedule that impact the schedules in self. Since
        # the state is not saved, it needs to recompute the quantity to
        # replenish of finished products. It will modify the indirect
        # demand and replenish_qty of schedules in self.
        # simulations_to_compute = self.env['dw.production.plan.simulation'].browse(self.get_impacted_schedule()) | self
        simulations_to_compute = self.env['dw.production.plan.simulation'].browse(self.ids) | self

        # Dependencies between schedules
        indirect_demand_trees = simulations_to_compute._get_indirect_demand_tree()

        # indirect_ratio_mps = simulations_to_compute._get_indirect_demand_ratio_mps(indirect_demand_trees)

        # Get the schedules that do not depend on one other in first position in
        # order to compute the schedule state only once.
        indirect_demand_order = simulations_to_compute._get_indirect_demand_order(indirect_demand_trees)
        indirect_demand_qty = defaultdict(float)
        incoming_qty, incoming_qty_done = self._get_incoming_qty(date_range)
        outgoing_qty, outgoing_qty_done = self._get_outgoing_qty(date_range)
        dummy, outgoing_qty_year_minus_1 = self._get_outgoing_qty(date_range_year_minus_1)
        dummy, outgoing_qty_year_minus_2 = self._get_outgoing_qty(date_range_year_minus_2)
        read_fields = [
            'safety_stock_target_qty',
            'min_to_replenish_qty',
            'max_to_replenish_qty',
            'product_id',
            'workcenter_id',
        ]
        if self.env.user.has_group('stock.group_stock_multi_warehouses'):
            read_fields.append('warehouse_id')
        if self.env.user.has_group('uom.group_uom'):
            read_fields.append('product_uom_id')
        production_simulation_states = simulations_to_compute.read(read_fields)
        production_simulation_states_by_id = {mps['id']: mps for mps in production_simulation_states}
        for production_simulation in indirect_demand_order:
            # Bypass if the schedule is only used in order to compute indirect
            # demand.
            rounding = production_simulation.product_id.uom_id.rounding
            lead_time = production_simulation._get_lead_times()
            # Ignore "Days to Supply Components" when set demand for components since it's normally taken care by the
            # components themselves
            lead_time_ignore_components = lead_time - production_simulation.bom_id.days_to_prepare_mo
            production_simulation_state = production_simulation_states_by_id[production_simulation['id']]
            if production_simulation in self:
                procurement_date = add(fields.Date.today(), days=lead_time)
                precision_digits = max(0, int(-(log10(production_simulation.product_uom_id.rounding))))
                production_simulation_state['precision_digits'] = precision_digits
                production_simulation_state['product_plan_sim_ids'] = []

            starting_inventory_qty = production_simulation.product_id.with_context(
                warehouse=production_simulation.warehouse_id.id).qty_available
            starting_inventory_qty_up = starting_inventory_qty
            if len(date_range):
                starting_inventory_qty -= incoming_qty_done.get(
                    (date_range[0], production_simulation.product_id, production_simulation.warehouse_id), 0.0)
                starting_inventory_qty += outgoing_qty_done.get(
                    (date_range[0], production_simulation.product_id, production_simulation.warehouse_id), 0.0)

                starting_inventory_qty_up = starting_inventory_qty
            for index, (date_start, date_stop) in enumerate(date_range):
                forecast_values = {}
                key = ((date_start, date_stop), production_simulation.product_id, production_simulation.warehouse_id)
                key_y_1 = (date_range_year_minus_1[index], *key[1:])
                key_y_2 = (date_range_year_minus_2[index], *key[1:])
                existing_forecasts = production_simulation.product_plan_sim_ids.filtered(
                    lambda p: p.date >= date_start and p.date <= date_stop)
                if production_simulation in self:
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

                    # ADDITION:
                    # forecast_values['sold_qty'] = float_round(outgoing_qty_done.get(key, 0.0),
                    #                                           precision_rounding=rounding)
                    # forecast_values['sale_objective_qty'] = float_round(
                    #     incoming_qty.get(key, 0.0), precision_rounding=rounding)
                    # forecast_values['production_objective_qty'] = float_round(
                    #     incoming_qty.get(key, 0.0), precision_rounding=rounding)

                forecast_values['indirect_demand_qty'] = float_round(indirect_demand_qty.get(key, 0.0),
                                                                     precision_rounding=rounding, rounding_method='UP')
                replenish_qty_updated = False
                if existing_forecasts:

                    forecast_values['sold_qty'] = float_round(sum(existing_forecasts.mapped('sold_qty')),
                                                              precision_rounding=rounding)

                    forecast_values['sale_objective_qty'] = float_round(
                        sum(existing_forecasts.mapped('sale_objective_qty')),
                        precision_rounding=rounding)

                    forecast_values['production_objective_qty'] = float_round(
                        sum(existing_forecasts.mapped('production_objective_qty')),
                        precision_rounding=rounding)

                    forecast_values['batch_count'] = float_round(
                        sum(existing_forecasts.mapped('batch_count')),
                        precision_rounding=rounding)

                    #     forecast_values['planned_production_qty'] = float_round(
                    #     sum(existing_forecasts.mapped('planned_production_qty')),
                    #     precision_rounding=rounding)

                    # forecast_values['stock_level'] = float_round(sum(existing_forecasts.mapped('stock_level')),
                    #                                              precision_rounding=rounding)

                    forecast_values['alert_notes'] = existing_forecasts[0].alert_notes or ''
                    forecast_values['notes'] = existing_forecasts[0].notes or ''

                    forecast_values['decision'] = existing_forecasts[0].dw_alert_decision_id.id or -1

                    forecast_values['forecasted_demand_qty'] = float_round(
                        sum(existing_forecasts.mapped('forecasted_demand_qty')),
                        precision_rounding=rounding)

                    forecast_values['replenish_qty'] = float_round(sum(existing_forecasts.mapped('replenish_qty')),
                                                                   precision_rounding=rounding)

                    # Check if the to replenish quantity has been manually set or
                    # if it needs to be computed.
                    replenish_qty_updated = any(existing_forecasts.mapped('replenish_qty_updated'))
                    forecast_values['replenish_qty_updated'] = replenish_qty_updated
                else:
                    forecast_values['forecasted_demand_qty'] = 0.0
                    forecast_values['sold_qty'] = 0.0
                    forecast_values['sale_objective_qty'] = 0.0
                    forecast_values['production_objective_qty'] = 0.0
                    # forecast_values['planned_production_qty'] = 0.0+
                    # forecast_values['stock_level'] = 0.0
                    forecast_values['batch_count'] = 0.0
                    forecast_values['alert_notes'] = ''
                    forecast_values['notes'] = ''

                if not replenish_qty_updated:
                    # starting_inventory_qty: starting_inventory_qty
                    # forecasted_demand_qty & indirect_demand_qty: sales forecast
                    # replenish_qty: net PPQty
                    # replenish_qty: ROUND UP net PPQty to lot size
                    # replenish_qty = production_simulation._get_replenish_qty(
                    #     starting_inventory_qty - forecast_values['forecasted_demand_qty'] - forecast_values[
                    #         'indirect_demand_qty'])
                    replenish_qty = production_simulation._get_replenish_qty(
                        starting_inventory_qty - production_simulation.sales_average)
                    forecast_values['replenish_qty'] = float_round(replenish_qty, precision_rounding=rounding)
                    forecast_values['replenish_qty_updated'] = False

                forecast_values['starting_inventory_qty'] = float_round(starting_inventory_qty,
                                                                        precision_rounding=rounding)

                forecast_values['starting_inventory_qty_up'] = float_round(starting_inventory_qty_up,
                                                                           precision_rounding=rounding)

                forecast_values['safety_stock_qty'] = float_round(
                    starting_inventory_qty - forecast_values['forecasted_demand_qty'] - forecast_values[
                        'indirect_demand_qty'] +
                    forecast_values['replenish_qty'], precision_rounding=rounding)

                # @bislem: Additions
                # forecast_values['stock_level'] = forecast_values['starting_inventory_qty']

                forecast_values['lot_size'] = production_simulation.lot_size

                forecast_values['batch_count'] = float_round(
                    sum(existing_forecasts.mapped('batch_count')),
                    precision_rounding=1, rounding_method='UP')

                forecast_values['suggested_production_plan_qty'] = (
                        forecast_values['batch_count'] * forecast_values['lot_size'])

                forecast_values['stock_level'] = (forecast_values['starting_inventory_qty'] -
                                                  production_simulation.sales_average)

                forecast_values['updated_stock_level'] = (forecast_values['starting_inventory_qty_up'] -
                                                          production_simulation.sales_average)

                forecast_values['planned_production_qty'] = calculate_planned_production_qty(
                    forecast_values.get('stock_level'),
                    production_simulation.safety_stock_target_qty,
                    production_simulation.sales_average,
                    production_simulation.safety_stock_target,
                )

                forecast_values['eff_planned_production_qty'] = round_up_to_nearest(
                    forecast_values['planned_production_qty'],
                    production_simulation.lot_size)

                forecast_values['replenish_qty'] = forecast_values['eff_planned_production_qty']

                forecast_values['stock_level'] = forecast_values['stock_level'] + forecast_values[
                    'eff_planned_production_qty']

                forecast_values['safety_stock_qty'] = float_round(
                    starting_inventory_qty - production_simulation.sales_average +
                    forecast_values['eff_planned_production_qty'], precision_rounding=rounding)

                forecast_values['safety_stock_qty_up'] = float_round(
                    starting_inventory_qty_up - production_simulation.sales_average +
                    forecast_values['suggested_production_plan_qty'], precision_rounding=rounding)

                forecast_values['planned_production_batches'] = safe_divide(forecast_values['planned_production_qty'],
                                                                            forecast_values['lot_size'])

                forecast_values['eff_planned_production_batches'] = safe_divide(
                    forecast_values.get('eff_planned_production_qty'),
                    forecast_values['lot_size'])

                forecast_values['stock_coverage'] = safe_divide(
                    forecast_values['stock_level'],
                    production_simulation.sales_average)

                forecast_values['updated_stock_level'] = forecast_values['updated_stock_level'] + forecast_values[
                    'suggested_production_plan_qty']

                forecast_values['updated_stock_coverage'] = safe_divide(
                    forecast_values.get('updated_stock_level'),
                    production_simulation.sales_average)

                forecast_values['required_capacity'] = forecast_values.get('suggested_production_plan_qty', 0.0)

                forecast_values['capacity_utilisation'] = float_round(100 * safe_divide(
                    forecast_values.get('required_capacity', 0.0),
                    production_simulation.workcenter_default_capacity), precision_rounding=2)

                if production_simulation in self:
                    production_simulation_state['product_plan_sim_ids'].append(forecast_values)

                starting_inventory_qty = forecast_values['safety_stock_qty']
                starting_inventory_qty_up = forecast_values['safety_stock_qty_up']
                # starting_inventory_qty = forecast_values['updated_stock_level']
                if not forecast_values['replenish_qty']:
                    continue

                # Set the indirect demand qty for children schedules.
                # for (product, ratio) in indirect_ratio_mps[
                #     (production_simulation.warehouse_id, production_simulation.product_id)].items():
                #     related_date = max(subtract(date_start, days=lead_time_ignore_components), fields.Date.today())
                #     index = next(i for i, (dstart, dstop) in enumerate(date_range) if
                #                  related_date <= dstart or (related_date >= dstart and related_date <= dstop))
                #     related_key = (date_range[index], product, production_simulation.warehouse_id)
                #     indirect_demand_qty[related_key] += ratio * forecast_values['replenish_qty']

            if production_simulation in self:
                # The state is computed after all because it needs the final
                # quantity to replenish.
                forecasts_state = production_simulation._get_forecasts_state(production_simulation_states_by_id,
                                                                             date_range,
                                                                             procurement_date)
                forecasts_state = forecasts_state[production_simulation.id]
                for index, forecast_state in enumerate(forecasts_state):
                    production_simulation_state['product_plan_sim_ids'][index].update(forecast_state)

        _states = sorted([p for p in production_simulation_states if p['id'] in self.ids], key=lambda p: p['id'])
        return _states

    def remove_replenish_qty(self, date_index):
        """ Remove the quantity to replenish on the simulation cell.

        param date_index: index of the period used to find start and stop date
        where the manual replenish quantity should be removed.
        """
        date_start, date_stop = self.company_id._get_simulation_date_range()[date_index]
        product_plan_sim_ids = self.product_plan_sim_ids.filtered(lambda f:
                                                                  f.date >= date_start and f.date <= date_stop)
        product_plan_sim_ids.write({
            'replenish_qty': 0.0,
            'replenish_qty_updated': False,
        })
        return True

    def set_forecast_qty(self, date_index, quantity):
        """ Save the simulation quantity:

        params quantity: The new total forecasted quantity
        params date_index: The manufacturing period
        """
        # Get the last date of current period
        self.ensure_one()
        date_start, date_stop = self.company_id._get_simulation_date_range()[date_index]
        existing_forecast = self.product_plan_sim_ids.filtered(lambda f:
                                                               f.date >= date_start and f.date <= date_stop)
        quantity = float_round(float(quantity), precision_rounding=self.product_uom_id.rounding)
        quantity_to_add = quantity - sum(existing_forecast.mapped('forecasted_demand_qty'))
        if existing_forecast:
            new_qty = existing_forecast[0].forecasted_demand_qty + quantity_to_add
            new_qty = float_round(new_qty, precision_rounding=self.product_uom_id.rounding)
            existing_forecast[0].write({'forecasted_demand_qty': new_qty})
        else:
            existing_forecast.create({
                'forecasted_demand_qty': quantity,
                'date': date_stop,
                'replenish_qty': 0,
                'production_simulation_id': self.id
            })
        return True

    # region: @bislem: Mocked data inputs
    def set_sales_objective_qty(self, date_index, quantity):
        """ Save the simulation quantity:

        params quantity: The new total forecasted quantity
        params date_index: The manufacturing period
        """
        # Get the last date of current period
        self.ensure_one()
        date_start, date_stop = self.company_id._get_simulation_date_range()[date_index]
        existing_forecast = self.product_plan_sim_ids.filtered(lambda f:
                                                               f.date >= date_start and f.date <= date_stop)
        quantity = float_round(float(quantity), precision_rounding=self.product_uom_id.rounding)
        if existing_forecast:
            existing_forecast[0].write({'sale_objective_qty': quantity})
        else:
            existing_forecast.create({
                'sale_objective_qty': quantity,
                'date': date_stop,
                # 'replenish_qty': 0,
                'production_simulation_id': self.id
            })
        return True

    def set_production_objective_qty(self, date_index, quantity):
        """ Save the simulation production objective quantity:

        params quantity: The new total production objective quantity
        params date_index: The manufacturing period
        """
        self.ensure_one()
        date_start, date_stop = self.company_id._get_simulation_date_range()[date_index]
        existing_forecast = self.product_plan_sim_ids.filtered(lambda f:
                                                               f.date >= date_start and f.date <= date_stop)
        quantity = float_round(float(quantity), precision_rounding=self.product_uom_id.rounding)
        if existing_forecast:
            existing_forecast[0].write({'production_objective_qty': quantity})
        else:
            existing_forecast.create({
                'production_objective_qty': quantity,
                'date': date_stop,
                'production_simulation_id': self.id
            })
        return True

    def set_planned_production_qty(self, date_index, quantity):
        """ Save the simulation planned production quantity:

        params quantity: The new total planned production quantity
        params date_index: The manufacturing period
        """
        self.ensure_one()
        date_start, date_stop = self.company_id._get_simulation_date_range()[date_index]
        existing_forecast = self.product_plan_sim_ids.filtered(lambda f:
                                                               f.date >= date_start and f.date <= date_stop)
        quantity = float_round(float(quantity), precision_rounding=self.product_uom_id.rounding)
        if existing_forecast:
            existing_forecast[0].write({'planned_production_qty': quantity})
        else:
            existing_forecast.create({
                'planned_production_qty': quantity,
                'date': date_stop,
                'production_simulation_id': self.id
            })
        return True

    def set_sold_qty(self, date_index, quantity):
        """ Save the simulation sold quantity:

        params quantity: The new total sold quantity
        params date_index: The manufacturing period
        """
        self.ensure_one()
        date_start, date_stop = self.company_id._get_simulation_date_range()[date_index]
        existing_forecast = self.product_plan_sim_ids.filtered(lambda f:
                                                               f.date >= date_start and f.date <= date_stop)
        quantity = float_round(float(quantity), precision_rounding=self.product_uom_id.rounding)
        if existing_forecast:
            existing_forecast[0].write({'sold_qty': quantity})
        else:
            existing_forecast.create({
                'sold_qty': quantity,
                'date': date_stop,
                'production_simulation_id': self.id
            })
        return True

    def set_batch_count(self, date_index, batch_count):
        """ Save the simulation production plan batch count:

        params batch_count: The new total production plan batch count
        params date_index: The manufacturing period
        """
        self.ensure_one()
        date_start, date_stop = self.company_id._get_simulation_date_range()[date_index]
        existing_forecast = self.product_plan_sim_ids.filtered(lambda f:
                                                               f.date >= date_start and f.date <= date_stop)
        batch_count = float_round(float(batch_count), precision_rounding=self.product_uom_id.rounding)
        if existing_forecast:
            existing_forecast[0].write({'batch_count': batch_count})
        else:
            existing_forecast.create({
                'batch_count': batch_count,
                'date': date_stop,
                'production_simulation_id': self.id
            })
        return True

    def set_stock_level(self, date_index, quantity):
        """ Save the simulation stock level:

        params quantity: The new total stock level
        params date_index: The manufacturing period
        """
        self.ensure_one()
        date_start, date_stop = self.company_id._get_simulation_date_range()[date_index]
        existing_forecast = self.product_plan_sim_ids.filtered(lambda f:
                                                               f.date >= date_start and f.date <= date_stop)
        quantity = float_round(float(quantity), precision_rounding=self.product_uom_id.rounding)
        if existing_forecast:
            existing_forecast[0].write({'stock_level': quantity})
        else:
            existing_forecast.create({
                'stock_level': quantity,
                'date': date_stop,
                'production_simulation_id': self.id
            })
        return True

    def set_notes(self, date_start, date_stop, notes):
        """ Save the simulation notes:

        params notes: The new notes
        params date_index: The manufacturing period
        """
        # self.ensure_one()
        if date_start and date_stop:
            date_start = datetime.datetime.strptime(date_start, '%Y-%m-%d').date()
            date_stop = datetime.datetime.strptime(date_stop, '%Y-%m-%d').date()

            existing_forecasts = self.product_plan_sim_ids.filtered(lambda f:
                                                                    f.date >= date_start and f.date <= date_stop)
            if existing_forecasts:
                existing_forecasts.write({'alert_notes': notes})
            else:
                existing_forecasts.create({
                    'alert_notes': notes,
                    'date': date_stop,
                    'production_simulation_id': self.id
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

        # self.ensure_one()
        if date_start and date_stop:
            date_start = datetime.datetime.strptime(date_start, '%Y-%m-%d').date()
            date_stop = datetime.datetime.strptime(date_stop, '%Y-%m-%d').date()

            existing_forecasts = self.product_plan_sim_ids.filtered(lambda f: f.date >= date_start and
                                                                              f.date <= date_stop)
            if existing_forecasts:
                existing_forecasts.write({'dw_alert_decision_id': decision_id})
            elif decision_id is not None:
                existing_forecasts.create({
                    'dw_alert_decision_id': decision_id,
                    'date': date_stop,
                    'production_schedule_id': self.id
                })

        return True

    def set_production_plan_batch_notes(self, date_index, date_start, date_stop, notes):
        """ Save the simulation notes:

        params notes: The new notes
        params date_index: The manufacturing period
        """
        # self.ensure_one()
        if date_start and date_stop:
            date_start = datetime.datetime.strptime(date_start, '%Y-%m-%d').date()
            date_stop = datetime.datetime.strptime(date_stop, '%Y-%m-%d').date()

            existing_forecasts = self.product_plan_sim_ids.filtered(lambda f:
                                                                    f.date >= date_start and f.date <= date_stop)
            if existing_forecasts:
                existing_forecasts.write({'notes': notes})
            else:
                existing_forecasts.create({
                    'notes': notes,
                    'date': date_stop,
                    'production_simulation_id': self.id
                })

        return True

    # endregion: @bislem: Mocked data inputs

    def set_replenish_qty(self, date_index, quantity):
        """ Save the replenish quantity and mark the cells as manually updated.

        params quantity: The new quantity to replenish
        params date_index: The manufacturing period
        """
        # Get the last date of current period
        self.ensure_one()
        date_start, date_stop = self.company_id._get_simulation_date_range()[date_index]
        existing_forecast = self.product_plan_sim_ids.filtered(lambda f:
                                                               f.date >= date_start and f.date <= date_stop)
        quantity = float_round(float(quantity), precision_rounding=self.product_uom_id.rounding)
        quantity_to_add = quantity - sum(existing_forecast.mapped('replenish_qty'))
        if existing_forecast:
            new_qty = existing_forecast[0].replenish_qty + quantity_to_add
            new_qty = float_round(new_qty, precision_rounding=self.product_uom_id.rounding)
            existing_forecast[0].write({
                'replenish_qty': new_qty,
                'replenish_qty_updated': True
            })
        else:
            existing_forecast.create({
                'forecasted_demand_qty': 0,
                'date': date_stop,
                'replenish_qty': quantity,
                'replenish_qty_updated': True,
                'production_simulation_id': self.id
            })
        return True

    def _filter_moves(self, moves_by_date, date_start, date_stop):
        return self.env['stock.move'].concat(*[m[0] for m in moves_by_date if m[1] >= date_start and m[1] <= date_stop])

    def _filter_rfq(self, rfq_by_date_planned, date_start, date_stop):
        return self.env['purchase.order.line'].concat(
            *[pl[0] for pl in rfq_by_date_planned if pl[1] >= date_start and pl[1] <= date_stop])

    def _get_procurement_extra_values(self, forecast_values):
        """ Extra values that could be added in the vals for procurement.

        return values pass to the procurement run method.
        rtype dict
        """
        return {
            'date_planned': forecast_values['date_start'],
            'warehouse_id': self.warehouse_id,
        }

    def _get_forecasts_state(self, production_simulation_states, date_range, procurement_date):
        """ Return the state for each simulation cells.
        - to_relaunch: A procurement has been launched for the same date range
        but a replenish modification require a new procurement.
        - to_correct: The actual replenishment is greater than planned, the MPS
        should be updated in order to match reality.
        - launched: Nothing todo. Either the cell is in the lead time range but
        the simulation match the actual replenishment. Or a foreced replenishment
        happens but the simulation and the actual demand still the same.
        - to_launch: The actual replenishment is lower than forecasted.

        It also add a tag on cell in order to:
        - to_replenish: The cell is to launch and it needs to be runned in order
        to arrive on time due to lead times.
        - forced_replenish: Cell to_launch or to_relaunch with the smallest
        period

        param production_simulation_states: schedules with a state to compute
        param date_range: list of period where a state should be computed
        param procurement_date: today + lead times for products in self
        return: the state for each time slot in date_range for each schedule in
        production_simulation_states
        rtype: dict
        """
        forecasts_state = defaultdict(list)
        for production_simulation in self:
            forecast_values = production_simulation_states[production_simulation.id]['product_plan_sim_ids']
            forced_replenish = True
            for index, (date_start, date_stop) in enumerate(date_range):
                forecast_state = {}
                forecast_value = forecast_values[index]
                existing_forecasts = production_simulation.product_plan_sim_ids.filtered(
                    lambda p: p.date >= date_start and p.date <= date_stop)
                # procurement_launched = any(existing_forecasts.mapped('procurement_launched'))

                replenish_qty = forecast_value['replenish_qty']
                incoming_qty = forecast_value['incoming_qty']
                # if incoming_qty < replenish_qty and procurement_launched:
                if incoming_qty < replenish_qty:
                    state = 'to_relaunch'
                elif incoming_qty > replenish_qty:
                    state = 'to_correct'
                # elif incoming_qty == replenish_qty and (date_start <= procurement_date or procurement_launched):
                elif incoming_qty == replenish_qty and (date_start <= procurement_date):
                    state = 'launched'
                else:
                    state = 'to_launch'
                forecast_state['state'] = state

                forecast_state['forced_replenish'] = False
                forecast_state['to_replenish'] = False

                procurement_qty = replenish_qty - incoming_qty
                if forecast_state['state'] not in ('launched', 'to_correct') and procurement_qty > 0:
                    if date_start <= procurement_date:
                        forecast_state['to_replenish'] = True
                    if forced_replenish:
                        forecast_state['forced_replenish'] = True
                        forced_replenish = False

                forecasts_state[production_simulation.id].append(forecast_state)
        return forecasts_state

    def _get_lead_times(self):
        """ Get the lead time for each product in self. The lead times are
        based on rules lead times + produce delay or supplier info delay.
        """
        rules = self.product_id._get_rules_from_location(self.warehouse_id.lot_stock_id)
        return rules._get_lead_days(self.product_id, bom=self.bom_id)[0]['total_delay']

    def _get_replenish_qty(self, after_forecast_qty):
        """ Modify the quantity to replenish depending on the min/max and targeted
        quantity for safety stock.

        param after_forecast_qty: The quantity to replenish in order to reach a
        safety stock of 0.
        return: quantity to replenish
        rtype: float
        """
        optimal_qty = self.safety_stock_target_qty - after_forecast_qty

        optimal = calculate_planned_production_qty(
            after_forecast_qty,
            self.safety_stock_target_qty,
            self.sales_average,
            self.safety_stock_target,
        )

        return optimal

        if optimal_qty > self.max_to_replenish_qty:
            replenish_qty = self.max_to_replenish_qty
        elif optimal_qty <= 0:
            replenish_qty = 0
        elif optimal_qty < self.min_to_replenish_qty:
            replenish_qty = self.min_to_replenish_qty
        else:
            replenish_qty = optimal_qty

        return replenish_qty

    def _get_incoming_qty(self, date_range):
        """ Get the incoming quantity from RFQ and existing moves.

        param: list of time slots used in order to group incoming quantity.
        return: a dict with as key a production schedule and as values a list
        of incoming quantity for each date range.
        """
        incoming_qty = defaultdict(float)
        incoming_qty_done = defaultdict(float)
        after_date = date_range[0][0]
        before_date = date_range[-1][1]
        # Get quantity in RFQ
        rfq_domain = self._get_rfq_domain(after_date, before_date)
        rfq_lines_date_planned = self._get_rfq_and_planned_date(rfq_domain, order='date_planned')
        rfq_lines_date_planned = sorted(rfq_lines_date_planned, key=lambda i: i[1])
        index = 0
        for (line, date_planned) in rfq_lines_date_planned:
            # There are cases when we want to consider rfq_lines where their date_planned occurs before the after_date
            # if lead times make their stock arrive at a relevant time. Therefore we need to ignore the simulationLines that have
            # date_planned + lead time < after_date
            if date_planned < after_date:
                continue
            # Skip to the next time range if the planned date is not in the
            # current time interval.

            while not (date_range[index][0] <= date_planned and
                       date_range[index][1] >= date_planned):
                index += 1
            quantity = line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id)
            incoming_qty[date_range[index], line.product_id, line.order_id.picking_type_id.warehouse_id] += quantity

        # Get quantity on incoming moves
        # TODO: issue since it will use one search by move. Should use a
        # read_group with a group by location.
        domain_moves = self._get_moves_domain(after_date, before_date, 'incoming')
        stock_moves_and_date = self._get_moves_and_date(domain_moves)
        stock_moves_and_date = sorted(stock_moves_and_date, key=lambda m: m[1])
        index = 0
        for (move, date) in stock_moves_and_date:
            if date < after_date or date > before_date:
                continue
            # Skip to the next time range if the planned date is not in the
            # current time interval.
            while not (date_range[index][0] <= date and date_range[index][1] >= date):
                index += 1
            key = (date_range[index], move.product_id, move.location_dest_id.warehouse_id)
            if move.state == 'done':
                incoming_qty_done[key] += move.product_qty
            else:
                incoming_qty[key] += move.product_qty

        return incoming_qty, incoming_qty_done

    def _get_indirect_demand_order(self, indirect_demand_trees):
        """ return a new order for record in self. The order returned ensure
        that the indirect demand from a record in the set could only be modified
        by a record before it. The purpose of this function is to define the
        states of multiple schedules only once by schedule and avoid to
        recompute a state because its indirect demand was a depend from another
        schedule.
        """
        product_ids = self.mapped('product_id')

        def _get_pre_order(node):
            order_list = []
            if node.product in product_ids:
                order_list.append(node.product)
            for child in node.children:
                order_list += _get_pre_order(child)
            return order_list

        product_order_by_tree = []
        for node in indirect_demand_trees:
            product_order_by_tree += _get_pre_order(node)

        product_order = OrderedDict()
        for product in reversed(product_order_by_tree):
            if product not in product_order:
                product_order[product] = True

        mps_order_by_product = defaultdict(lambda: self.env['dw.production.plan.simulation'])
        for mps in self:
            mps_order_by_product[mps.product_id] |= mps

        mps_order = self.env['dw.production.plan.simulation']
        for product in reversed(product_order.keys()):
            mps_order |= mps_order_by_product[product]
        return mps_order

    def _get_indirect_demand_ratio_mps(self, indirect_demand_trees):
        """ Return {(warehouse, product): {product: ratio}} dict containing the indirect ratio
        between two products.
        """
        by_warehouse_mps = defaultdict(lambda: self.env['dw.production.plan.simulation'])
        for mps in self:
            by_warehouse_mps[mps.warehouse_id] |= mps

        result = defaultdict(lambda: defaultdict(float))
        for warehouse_id, other_mps in by_warehouse_mps.items():
            other_mps_product_ids = other_mps.mapped('product_id')
            subtree_visited = set()

            def _dfs_ratio_search(current_node, ratio, node_indirect=False):
                for child in current_node.children:
                    if child.product in other_mps_product_ids:
                        result[(warehouse_id, node_indirect and node_indirect.product or current_node.product)][
                            child.product] += ratio * child.ratio
                        if child.product in subtree_visited:  # Don't visit the same subtree twice
                            continue
                        subtree_visited.add(child.product)
                        _dfs_ratio_search(child, 1.0, node_indirect=False)
                    else:  # Hidden Bom => continue DFS and set node_indirect
                        _dfs_ratio_search(child, child.ratio * ratio, node_indirect=current_node)

            for tree in indirect_demand_trees:
                _dfs_ratio_search(tree, tree.ratio)

        return result

    def _get_indirect_demand_tree(self):
        """ Get the tree architecture for all the BoM and BoM line that are
        related to production schedules in self. The purpose of the tree:
        - Easier traversal than with BoM and BoM simulationLines.
        - Allow to determine the schedules evaluation order. (compute the
        schedule without indirect demand first)
        It also made the link between schedules even if some intermediate BoM
        levels are hidden. (e.g. B1 -1-> B2 -1-> B3, schedule for B1 and B3
        are linked even if the schedule for B2 does not exist.)
        Return a list of namedtuple that represent on top the schedules without
        indirect demand and on lowest leaves the schedules that are the most
        influenced by the others.
        """
        bom_by_product = self.env['mrp.bom']._bom_find(self.product_id)

        Node = namedtuple('Node', ['product', 'ratio', 'children'])
        indirect_demand_trees = {}
        product_visited = {}

        def _get_product_tree(product, ratio):
            product_tree = product_visited.get(product)
            if product_tree:
                return Node(product_tree.product, ratio, product_tree.children)

            product_tree = Node(product, ratio, [])
            product_bom = bom_by_product.get(product)
            if product not in bom_by_product and not product_bom:
                product_bom = self.env['mrp.bom']._bom_find(product)[product]
            for line in product_bom.bom_line_ids:
                if line._skip_bom_line(product):
                    continue
                line_qty = line.product_uom_id._compute_quantity(line.product_qty, line.product_id.uom_id)
                bom_qty = line.bom_id.product_uom_id._compute_quantity(line.bom_id.product_qty,
                                                                       line.bom_id.product_tmpl_id.uom_id)
                ratio = line_qty / bom_qty
                tree = _get_product_tree(line.product_id, ratio)
                product_tree.children.append(tree)
                if line.product_id in indirect_demand_trees:
                    del indirect_demand_trees[line.product_id]
            product_visited[product] = product_tree
            return product_tree

        for product in self.mapped('product_id'):
            if product in product_visited:
                continue
            indirect_demand_trees[product] = _get_product_tree(product, 1.0)

        return [tree for tree in indirect_demand_trees.values()]

    def _get_moves_domain(self, date_start, date_stop, type):
        """ Return domain for incoming or outgoing moves """
        if not self:
            return [('id', '=', False)]
        location = type == 'incoming' and 'location_dest_id' or 'location_id'
        location_dest = type == 'incoming' and 'location_id' or 'location_dest_id'
        domain = []
        common_domain = [
            ('state', 'not in', ['cancel', 'draft']),
            (location + '.usage', '!=', 'inventory'),
            '|',
            (location_dest + '.usage', 'not in', ('internal', 'inventory')),
            '&',
            (location_dest + '.usage', '=', 'internal'),
            '!',
            (location_dest, 'child_of', self.mapped('warehouse_id.view_location_id').ids),
            ('is_inventory', '=', False),
            ('date', '<=', date_stop),
        ]
        groupby_delay = defaultdict(list)
        for schedule in self:
            rules = schedule.product_id._get_rules_from_location(schedule.warehouse_id.lot_stock_id)
            lead_days, dummy = rules.filtered(lambda r: r.action not in ['buy', 'manufacture'])._get_lead_days(
                schedule.product_id)
            delay = lead_days['total_delay']
            groupby_delay[delay].append((schedule.product_id, schedule.warehouse_id))
        for delay in groupby_delay:
            products, warehouses = zip(*groupby_delay[delay])
            warehouses = self.env['stock.warehouse'].concat(*warehouses)
            products = self.env['product.product'].concat(*products)
            specific_domain = [
                (location, 'child_of', warehouses.mapped('view_location_id').ids),
                ('product_id', 'in', products.ids),
                ('date', '>=', date_start - relativedelta(days=delay)),
            ]
            domain = OR([domain, AND([common_domain, specific_domain])])
        return domain

    @api.model
    def _get_dest_moves_delay(self, move, delay=0):
        if move.origin_returned_move_id:
            return delay
        elif not move.move_dest_ids:
            return delay + move.rule_id.delay
        else:
            delays = []
            additional_delay = move.rule_id.delay
            for move_dest in move.move_dest_ids:
                delays.append(self._get_dest_moves_delay(
                    move_dest, delay=delay + additional_delay))
            return max(delays)

    def _get_moves_and_date(self, moves_domain, order=False):
        moves = self.env['stock.move'].search(moves_domain, order=order)
        res_moves = []
        for move in moves:
            delay = self._get_dest_moves_delay(move)
            date = fields.Date.to_date(move.date) + relativedelta(days=delay)
            res_moves.append((move, date))
        return res_moves

    def _get_outgoing_qty(self, date_range):
        """ Get the outgoing quantity from existing moves.
        return a dict with as key a production schedule and as values a list
        of outgoing quantity for each date range.
        """
        outgoing_qty = defaultdict(float)
        outgoing_qty_done = defaultdict(float)
        after_date = date_range[0][0]
        before_date = date_range[-1][1]
        # Get quantity on incoming moves

        domain_moves = self._get_moves_domain(after_date, before_date, 'outgoing')
        domain_moves = AND([domain_moves, [('raw_material_production_id', '=', False)]])
        stock_moves_by_date = self._get_moves_and_date(domain_moves)
        stock_moves_by_date = sorted(stock_moves_by_date, key=lambda m: m[1])
        index = 0
        for (move, date) in stock_moves_by_date:
            # There are cases when we want to consider moves where their (scheduled) date occurs before the after_date
            # if lead times make their stock delivery at a relevant time. Therefore we need to ignore the simulationLines that have
            # date + lead time < after_date. Similar logic with before_date
            if date < after_date or date > before_date:
                continue
            # Skip to the next time range if the planned date is not in the
            # current time interval.
            while not (date_range[index][0] <= date and date_range[index][1] >= date):
                index += 1
            key = (date_range[index], move.product_id, move.location_id.warehouse_id)
            if move.state == 'done':
                outgoing_qty_done[key] += move.product_uom_qty
            else:
                outgoing_qty[key] += move.product_uom_qty

        return outgoing_qty, outgoing_qty_done

    def _get_rfq_domain(self, date_start, date_stop):
        """ Return a domain used to compute the incoming quantity for a given
        product/warehouse/company.

        :param date_start: start date of the simulation domain
        :param date_stop: end date of the simulation domain
        """
        if not self:
            return [('id', '=', False)]
        domain = []
        common_domain = [
            ('state', 'in', ('draft', 'sent', 'to approve')),
            ('date_planned', '<=', date_stop)
        ]
        groupby_delay = defaultdict(list)
        for schedule in self:
            rules = schedule.product_id._get_rules_from_location(schedule.warehouse_id.lot_stock_id)
            lead_days, dummy = rules._get_lead_days(schedule.product_id)
            delay = lead_days['total_delay']
            groupby_delay[delay].append((schedule.product_id, schedule.warehouse_id))

        for delay in groupby_delay:
            products, warehouses = zip(*groupby_delay[delay])
            warehouses = self.env['stock.warehouse'].concat(*warehouses)
            products = self.env['product.product'].concat(*products)
            specific_domain = [
                ('order_id.picking_type_id.default_location_dest_id', 'child_of',
                 warehouses.mapped('view_location_id').ids),
                ('product_id', 'in', products.ids),
                ('date_planned', '>=', date_start - relativedelta(days=delay)),
            ]
            domain = OR([domain, AND([common_domain, specific_domain])])
        return domain

    def _get_rfq_and_planned_date(self, rfq_domain, order=False):
        purchase_lines = self.env['purchase.order.line'].search(rfq_domain, order=order)
        res_purchase_lines = []
        for line in purchase_lines:
            if not line.move_dest_ids:
                res_purchase_lines.append((line, fields.Date.to_date(line.date_planned)))
                continue
            delay = max(map(self._get_dest_moves_delay, line.move_dest_ids))
            date = fields.Date.to_date(line.date_planned) + relativedelta(days=delay)
            res_purchase_lines.append((line, date))

        return res_purchase_lines

    def get_impacted_schedule(self, domain=False):
        """ When the user modify the demand simulation on a schedule. The new
        replenish quantity is computed from schedules that use the product in
        self as component (no matter at which BoM level). It will also modify
        the replenish quantity on self that will impact the schedule that use
        the product in self as a finished product.

        :param domain: filter supplied and supplying schedules with the domain
        :return ids of supplied and supplying schedules
        :rtype list
        """
        if not domain:
            domain = []

        # def _used_in_bom(products, related_products):
        #     """ Bottom up from bom line to finished products in order to get
        #     all the finished products that use 'products' as component.
        #     """
        #     if not products:
        #         return related_products
        #     boms = products.bom_line_ids.mapped('bom_id')
        #     products = boms.mapped('product_id') | boms.mapped('product_tmpl_id.product_variant_ids')
        #     products -= related_products
        #     related_products |= products
        #     return _used_in_bom(products, related_products)

        supplying_mps = self.env['dw.production.plan.simulation'].search(
            AND([domain, [
                ('warehouse_id', 'in', self.mapped('warehouse_id').ids),
                ('product_id', 'in', self.mapped('product_id').ids)
            ]]))

        # def _use_boms(products, related_products):
        #     """ Explore bom line from products's BoMs in order to get components
        #     used.
        #     """
        #     if not products:
        #         return related_products
        #     components = products.mapped(lambda product: product.bom_ids.bom_line_ids.filtered(
        #         lambda line: not line._skip_bom_line(product)).mapped('product_id'))
        #
        #     components -= related_products
        #     related_products |= components
        #     return _use_boms(components, related_products)
        #
        # supplied_mps = self.env['dw.production.plan.simulation'].search(
        #     AND([domain, [
        #         ('warehouse_id', 'in', self.mapped('warehouse_id').ids),
        #         ('product_id', 'in', _use_boms(self.mapped('product_id'), self.env['product.product']).ids)
        #     ]]))
        # return (supplying_mps | supplied_mps).ids
        return supplying_mps.ids

    def _query(self, product_id):
        _QUERY = """
                    
            SELECT 
            MIN(l.id) AS id,
            l.product_id AS product_id,
            t.uom_id AS product_uom,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(l.product_uom_qty / u.factor * u2.factor) ELSE 0 END AS product_uom_qty,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(l.qty_delivered / u.factor * u2.factor) ELSE 0 END AS qty_delivered,
            CASE WHEN l.product_id IS NOT NULL THEN SUM((l.product_uom_qty - l.qty_delivered) / u.factor * u2.factor) ELSE 0 END AS qty_to_deliver,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(l.qty_invoiced / u.factor * u2.factor) ELSE 0 END AS qty_invoiced,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(l.qty_to_invoice / u.factor * u2.factor) ELSE 0 END AS qty_to_invoice,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(l.price_total
                / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END
                * CASE COALESCE(currency_table.rate, 0) WHEN 0 THEN 1.0 ELSE currency_table.rate END
                ) ELSE 0
            END AS price_total,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(l.price_subtotal
                / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END
                * CASE COALESCE(currency_table.rate, 0) WHEN 0 THEN 1.0 ELSE currency_table.rate END
                ) ELSE 0
            END AS price_subtotal,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(l.untaxed_amount_to_invoice
                / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END
                * CASE COALESCE(currency_table.rate, 0) WHEN 0 THEN 1.0 ELSE currency_table.rate END
                ) ELSE 0
            END AS untaxed_amount_to_invoice,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(l.untaxed_amount_invoiced
                / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END
                * CASE COALESCE(currency_table.rate, 0) WHEN 0 THEN 1.0 ELSE currency_table.rate END
                ) ELSE 0
            END AS untaxed_amount_invoiced,
            COUNT(*) AS nbr,
            s.name AS name,
            s.date_order AS date,
            s.state AS state,
            s.invoice_status as invoice_status,
            s.partner_id AS partner_id,
            s.user_id AS user_id,
            s.company_id AS company_id,
            s.campaign_id AS campaign_id,
            s.medium_id AS medium_id,
            s.source_id AS source_id,
            t.categ_id AS categ_id,
            s.pricelist_id AS pricelist_id,
            s.analytic_account_id AS analytic_account_id,
            s.team_id AS team_id,
            p.product_tmpl_id,
            partner.commercial_partner_id AS commercial_partner_id,
            partner.country_id AS country_id,
            partner.industry_id AS industry_id,
            partner.state_id AS state_id,
            partner.zip AS partner_zip,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(p.weight * l.product_uom_qty / u.factor * u2.factor) ELSE 0 END AS weight,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(p.volume * l.product_uom_qty / u.factor * u2.factor) ELSE 0 END AS volume,
            l.discount AS discount,
            CASE WHEN l.product_id IS NOT NULL THEN SUM(l.price_unit * l.product_uom_qty * l.discount / 100.0
                / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END
                * CASE COALESCE(currency_table.rate, 0) WHEN 0 THEN 1.0 ELSE currency_table.rate END
                ) ELSE 0
            END AS discount_amount,
            concat('sale.order', ',', s.id) AS order_reference,
            s.warehouse_id AS warehouse_id,
            SUM(l.margin
            / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END
            * CASE COALESCE(currency_table.rate, 0) WHEN 0 THEN 1.0 ELSE currency_table.rate END)
         AS margin
            FROM 
            sale_order_line l
            LEFT JOIN sale_order s ON s.id=l.order_id
            JOIN res_partner partner ON s.partner_id = partner.id
            LEFT JOIN product_product p ON l.product_id=p.id
            LEFT JOIN product_template t ON p.product_tmpl_id=t.id
            LEFT JOIN uom_uom u ON u.id=l.product_uom
            LEFT JOIN uom_uom u2 ON u2.id=t.uom_id
            JOIN (VALUES (1, 1.0, 2)) AS currency_table(company_id, rate, precision) ON currency_table.company_id = s.company_id
            
            WHERE 
            l.display_type IS NULL and s.state = 'sale' and l.product_id = {product_id}
            GROUP BY 
            l.product_id,
            l.order_id,
            t.uom_id,
            t.categ_id,
            s.name,
            s.date_order,
            s.partner_id,
            s.user_id,
            s.state,
            s.invoice_status,
            s.company_id,
            s.campaign_id,
            s.medium_id,
            s.source_id,
            s.pricelist_id,
            s.analytic_account_id,
            s.team_id,
            p.product_tmpl_id,
            partner.commercial_partner_id,
            partner.country_id,
            partner.industry_id,
            partner.state_id,
            partner.zip,
            l.discount,
            s.id,
            currency_table.rate,
            s.warehouse_id
        """.format(
            product_id=product_id
        )
        return _QUERY

    def _sales_query(self, query_str):
        res = self.env.cr.execute(query_str)

        result = {}
        _results = self.env.cr.dictfetchall()

        for row in _results:
            print(row)

        return _results

    def calculate_average_qty_to_deliver(self, data, start_date=None, end_date=None):
        """
        Calculate the average of the 'qty_to_deliver' field in a list of dictionaries.

        Args:
            data (list of dict): The list of dictionaries containing the data.
            start_date (datetime.datetime, optional): The start date for the date range filter.
            end_date (datetime.datetime, optional): The end date for the date range filter.

        Returns:
            float: The average of the 'qty_to_deliver' field.
        """
        filtered_data = data
        if start_date and end_date:
            filtered_data = [item for item in data if
                             start_date <= item.get('date').date() <= end_date]

        if filtered_data:
            return safe_divide(sum(item.get('qty_to_deliver', 0.0) for item in filtered_data), len(filtered_data))
        else:
            return safe_divide(sum(item.get('qty_to_deliver', 0.0) for item in data), len(data))


class DwProductPlanSimulation(models.Model):
    _name = 'dw.product.production.plan.simulation'
    _order = 'date'
    _description = "Product's Production Plan Simulation at Date"

    production_simulation_id = fields.Many2one('dw.production.plan.simulation', required=True, ondelete='cascade')
    date = fields.Date('Date', required=True)

    forecasted_demand_qty = fields.Float('Demand Forecast', default=0.0)
    replenish_qty_updated = fields.Boolean('Replenish_qty has been manually updated')
    # procurement_launched = fields.Boolean('Procurement has been run for this simulation')

    sale_objective_qty = fields.Float('Sales Objective Qty', default=0.0)
    production_objective_qty = fields.Float('Production Objective Qty', default=0.0)

    planned_production_qty = fields.Float('Planned Production Qty', default=0.0,
                                          compute='_compute_planned_production_qty')

    sold_qty = fields.Float('Sales Qty', default=0.0)

    stock_level = fields.Float('stock_level', default=0.0)

    batch_count = fields.Float('Batches Count', default=0.0)

    replenish_qty = fields.Float('Qty To Produce', default=0.0)

    dw_alert_decision_id = fields.Many2one('dw.mrp.alert.decision', string='Decision')

    notes = fields.Text('Observations')

    alert_notes = fields.Text('Alert Observations')

    @api.depends('stock_level', 'production_simulation_id.safety_stock_target_qty',
                 'production_simulation_id.sales_average')
    def _compute_planned_production_qty(self):
        for record in self:
            record.planned_production_qty = calculate_planned_production_qty(record.stock_level,
                                                                             record.production_simulation_id.safety_stock_target_qty,
                                                                             record.production_simulation_id.sales_average,
                                                                             record.production_simulation_id.safety_stock_target)
