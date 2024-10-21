# -*- coding: utf-8 -*-

from odoo import  fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


    module_dw_auto_generate_lot_number = fields.Boolean("Lot Auto generate")
