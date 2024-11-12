# -*- coding: utf-8 -*-


from odoo import api, fields, models
from odoo.tools.date_utils import end_of

__SEPARATOR__ = '- V'


class DwDwProductionPlanSimulationVersionTarget(models.Model):
    _inherit = 'dw.production.plan.simulation.version'

    target_id = fields.Many2one('dw.mrp.production.target', string="Production Targets Version", ondelete='cascade',
                                domain="[('company_id','=', company_id)]")

    @api.onchange('target_id')
    @api.depends('target_id')
    def _onchange_target_id(self):
        for record in self:
            if not record.target_id:
                continue

            # Loop through the simulations
            for simulation in record.simulation_ids:
                if not simulation:
                    continue

                # Filter product targets based on the current product_id
                relevant_targets = record.target_id.product_target_ids.filtered(
                    lambda t: t.product_id == simulation.product_id
                )

                # Check for empty list
                if not relevant_targets:
                    continue

                # Iterate over the relevant targets
                for product_target in relevant_targets:
                    if not product_target:
                        continue

                    # Loop through each product_plan_sim_ids in the simulation
                    for prduct_monthly_trgt in product_target.product_monthly_target_ids:
                        _date = end_of(prduct_monthly_trgt.date, 'month')
                        existing_prdct_sim = simulation.product_plan_sim_ids.filtered(lambda f:
                                                                                      prduct_monthly_trgt.date <= f.date <= _date)
                        vals = {
                            'production_objective_qty': prduct_monthly_trgt.production_objective_qty,
                            'sale_objective_qty': prduct_monthly_trgt.sales_objective_qty
                        }
                        if existing_prdct_sim:
                            existing_prdct_sim[0].write(vals)
                        else:
                            vals.update({
                                'date': _date,
                                'production_simulation_id': simulation.ids[0]
                            })
                            existing_prdct_sim.create(vals)

            # Notify
            return {
                'warning': {
                    'title': "Objectives Updated",
                    'message': f"Production and Sales objectives have been updated based on the targets:\n {self.target_id.name}"
                }
            }

    def write(self, values):
        if values.get('target_id', False):
            # for record in self:
            #     values['name'] = '%s %s' % (
            #         values.get('first_name', False) or record.first_name or '',
            #         values.get('last_name', False) or record.last_name or '',
            #     )
            super(DwDwProductionPlanSimulationVersionTarget, self).write(values)
        else:
            super(DwDwProductionPlanSimulationVersionTarget, self).write(values)
