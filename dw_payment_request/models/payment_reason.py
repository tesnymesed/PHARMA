# -*- coding:utf-8 -*-

from odoo import fields, models, api, _


class DwPaymentReason(models.Model):
    _name = "dw.payment.reason"

    name = fields.Char( string='Name')
