from odoo import fields, models


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    dw_force_mrp_config = fields.Boolean("Force Configuration")
    dw_location_component_id = fields.Many2one("stock.location", string="Emplacement des composants")
    dw_location_dest_id = fields.Many2one("stock.location", string="Emplacement des PF")
    dw_majoration = fields.Float("Majoration")
    dw_mrp_forme_id = fields.Many2one("dw.mrp.bom.form", string='Forme')

    mrp_sublot_wizard_id = fields.Char("Sublot Wizard ID")

    tracking_type= fields.Selection([
        ('lot','Lot'),
        ('sublot','Sublot')
    ], string='Tracking By',default='lot',required=True)