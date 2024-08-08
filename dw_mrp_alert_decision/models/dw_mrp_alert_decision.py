from odoo import fields, models


class DwProductPlanSimulationDecision(models.Model):
    _name = 'dw.mrp.alert.decision'
    _order = 'sequence'
    _description = "MRP Alert Decision"

    name = fields.Char(string='Decision', required=True)
    sequence = fields.Integer(string='Sequence', default=10)

    def get_decision_action_items(self):
        _self = self.search([])

        r = {rec.id: rec.name for rec in _self}
        r.update({-1: ' '})
        return r
