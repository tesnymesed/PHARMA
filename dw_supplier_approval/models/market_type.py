# -*- coding:utf-8 -*-

from odoo import fields, models


class DwMarketType(models.Model):
    _name = 'dw.market.type'
    name = fields.Char(string="Name", required=True)
    code = fields.Char( string="Code")

