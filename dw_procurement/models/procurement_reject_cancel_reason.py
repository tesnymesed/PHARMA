from odoo import models, fields

class ProcurementRejectCancelReason(models.Model):
    _name = 'procurement.reject.cancel.reason'
    _description = 'Procurement Reject or Cancel Reason'

    name = fields.Char(string='Reason', required=True)
    reason_type = fields.Selection([
        ('reject', 'Reject'),
        ('cancel', 'Cancel')
    ], string='Type', required=True, default='reject')
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)