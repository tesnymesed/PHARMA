from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class DwConsultationCriteria(models.Model):
    _inherit = 'procurement.dw.consultation'


    approval_id = fields.Many2one('procurement.supplier.approval', string='approval',
                                  domain="[('state','in',['approval'])]")


    def action_show_approval(self):
        self.ensure_one()
        return ({
            'res_model': 'procurement.supplier.approval',
            'type': 'ir.actions.act_window',
            'name': _("%(consultation_name)s's Consultations", consultation_name=self.name),

            'domain': [
                ('consultation_ids', 'in', self.id),
            ],
            'view_mode': 'tree,form',

            'context': {'create': False},
        })
