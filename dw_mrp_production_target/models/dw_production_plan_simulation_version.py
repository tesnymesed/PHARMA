# -*- coding: utf-8 -*-


from odoo import api, fields, models

__SEPARATOR__ = '- V'


class DwDwProductionPlanSimulationVersionTarget(models.Model):
    _inherit = 'dw.production.plan.simulation.version'

    target_id = fields.Many2one('dw.mrp.production.target', string="Production Targets Version", ondelete='cascade',
                                domain="[('company_id','=', company_id)]")

    @api.onchange('target_id')
    @api.depends('target_id')
    def _onchange_target_id(self):
        for record in self:
            if record.target_id:

                # Loop through the simulations
                for simulation in record.simulation_ids:
                    # Filter product targets based on the current product_id
                    relevant_targets = record.target_id.product_target_ids.filtered(
                        lambda t: t.product_id == simulation.product_id
                    )

                    # Iterate over the relevant targets
                    for product_target in relevant_targets:
                        # Loop through each product_plan_sim_ids in the simulation
                        for plan_sim in simulation.product_plan_sim_ids:
                            # Filter monthly targets based on the matching date
                            matching_monthly_targets = product_target.product_monthly_target_ids.filtered(
                                lambda mt: mt.date == plan_sim.date
                            )

                            # Update the objective quantities from the matching monthly targets
                            for monthly_target in matching_monthly_targets:
                                simulation.production_objective_qty = monthly_target.production_objective_qty
                                simulation.sale_objective_qty = monthly_target.sales_objective_qty

                # Inform the user
                return {
                    'warning': {
                        'title': "Objectives Updated",
                        'message': "Production and Sales objectives have been updated based on the target.",
                    }
                }

    def write(self, values):
        if values.get('target_id', False):
            for record in self:
                values['name'] = '%s %s' % (
                    values.get('first_name', False) or record.first_name or '',
                    values.get('last_name', False) or record.last_name or '',
                )
                super(DwDwProductionPlanSimulationVersionTarget, record).write(values)
        else:
            super(DwDwProductionPlanSimulationVersionTarget, self).write(values)