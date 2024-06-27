from odoo import fields, models, api, _


class HomologationResPartner(models.Model):
    _inherit = 'res.partner'

    def action_show_homologations(self):
        return ({
            'res_model': 'dw.homologation',
            'type': 'ir.actions.act_window',
            'name': _("%(supplier_name)s's homologation", supplier_name=self.name),

            'domain': [
                ('supplier_id', '=', self.id),
            ],
            'view_mode': 'tree,form',

            'context': {"create": 0},
        })
