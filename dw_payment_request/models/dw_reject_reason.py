# -*- coding:utf-8 -*-

from odoo import fields, models, api, _


class DwRejectReason(models.Model):
    _name = "dw.reject.reason"

    name = fields.Char('Reject Reason')

