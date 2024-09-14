# -*- coding:utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class DwMarketType(models.Model):
    _name = 'procurement.market.dw.type'
    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code")
    forced_nbr_supplier = fields.Boolean("Forcing Number of supplier ?", default=False)
    nbr_supplier = fields.Integer("Forcing Number", default=0)

    @api.constrains('forced_nbr_supplier', "nbr_supplier")
    def _check_nbr_supplier(self):
        if any(record.forced_nbr_supplier and not record.nbr_supplier for record in self):
            raise ValidationError(
                _('The number of supplier must be greater than 0.!')
            )

    @api.onchange('forced_nbr_supplier')
    def onchange_forced_nbr_supplier(self):
        if not self.forced_nbr_supplier:
            self.nbr_supplier = 0
