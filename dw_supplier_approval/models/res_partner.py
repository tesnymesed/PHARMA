from odoo import fields, models, api, _


class approvalResPartner(models.Model):
    _inherit = 'res.partner'

    def action_show_approvals(self):
        return ({
            'res_model': 'procurement.supplier.approval',
            'type': 'ir.actions.act_window',
            'name': _("%(supplier_name)s's approval", supplier_name=self.name),

            'domain': [
                ('supplier_id', '=', self.id),
            ],
            'view_mode': 'tree,form',

            'context': {"create": 0},
        })
