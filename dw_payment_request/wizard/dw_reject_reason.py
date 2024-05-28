# -*- coding: utf-8 -*-
from odoo import fields, models


class DwRejectReason(models.TransientModel):
    _name = 'dw.reject.reason.wizard'

    payment_request_id = fields.Many2one('dw.payment.request' , string=" Payment request")
    date = fields.Date("Date")
    reject_motif_id = fields.Many2one('dw.reject.reason',string='Reject reason')

    def  action_confirm(self):
        self.payment_request_id.write({'state': 'rejected'})
        self.payment_request_id.write({'reject_motif_id': False, 'date': False})
        self.payment_request_id.write({'reject_motif_id':self.reject_motif_id , 'date':self.date})

