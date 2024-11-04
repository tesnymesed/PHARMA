from odoo import fields, api, models
from odoo.exceptions import ValidationError


class MrpPlan(models.Model):
    _inherit = 'mrp.plan'

    # New Fields
    simulation_version_id = fields.Many2one('dw.production.plan.simulation.version', string='Production Plan Simulation Version',
                                 help="Reference to the production plan simulation version.")
    is_current = fields.Boolean('Is Current', default=False,
                                help="Marks this plan as the active or current plan for the version.")

    @api.constrains('is_current')
    def _check_unique_current(self):
        """Ensures only one current MrpPlan per ProductionSimulationVersion."""
        for plan in self:
            if plan.is_current:
                other_current = self.search([
                    ('simulation_version_id', '=', plan.simulation_version_id.id),
                    ('is_current', '=', True),
                    ('id', '!=', plan.id)
                ])
                if other_current:
                    # Generate an HTML list of other current plans
                    other_plan_names = "".join(f"<li>{p.name}</li>" for p in other_current)
                    error_message = f"Only one MRP plan can be set as current for each production version. The following plans are already set as current:<ul>{other_plan_names}</ul>"
                    raise ValidationError(error_message)
