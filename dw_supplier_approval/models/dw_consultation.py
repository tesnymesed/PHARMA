from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class DwConsultationCriteria(models.Model):
    _inherit = 'dw.consultation'

    market_id = fields.Many2one(domain="[('state','=','homologation_cosultation')]")
    supplier_market_id = fields.Many2many(related="market_id.supplier_homologuer_ids")
    homologation_ids = fields.Many2many(related="market_id.homologation_ids")
   
    homologation_id = fields.Many2one('dw.homologation', string='Homologation', domain="[('state','in',['homologue'])]")
    product_id = fields.Many2one(
        domain=['|', '|', ('homologue', '=', True), ('categ_id.homologue', '=', True),
                ('product_tmpl_id.homologue', '=', True), ('purchase_ok', '=', True)],

    )

    def action_show_homologation(self):
        return ({
            'res_model': 'dw.homologation',
            'type': 'ir.actions.act_window',
            'name': _("%(consultation_name)s's Consultations", consultation_name=self.name),

            'domain': [
                ('consultation_id', '=', self.id),
            ],
            'view_mode': 'tree,form',

            'context': {'create': False},
        })
