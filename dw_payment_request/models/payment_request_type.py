from odoo import models, fields

class PaymentRequestType(models.Model):
    _name = 'payment.request.type'
    _description = 'Payment Request Type'

    name = fields.Char(string='Nom', required=True)
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Description')
