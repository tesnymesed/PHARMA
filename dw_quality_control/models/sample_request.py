import datetime

from odoo import models, api, fields, _

class SampleRequest(models.Model):
    _name = 'sample.request'
    description = 'Request for a sample'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name')
    company_id = fields.Many2one('res.company',string='Company', default=lambda self: self.env.company)
    request_time = fields.Datetime(string="Request Time", tracking=True)
    user_id= fields.Many2one('res.users',string='Requested By',required=True, tracking=True)
    product_id = fields.Many2one('product.product',string='Product',required=True)
    lot_id = fields.Many2one('stock.lot',string='Lot/Serial')
    line_ids = fields.One2many('sample.request.lines','simple_request_id')
    validation_time = fields.Datetime(string='Validate Time', tracking=True)
    validation_by = fields.Many2one('res.users',string='Validate By', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('validate', 'Validated'),
        ('rejected', 'Rejected'),
        ('cancel', 'Canceled'),
    ], string='State', default='draft')

    def action_canceled(self):
        self.write({"state": 'cancel'})
        return {'type': 'ir.actions.act_window_close'}

    def action_reject(self):
        self.write({"state": 'rejected'})
        return {'type': 'ir.actions.act_window_close'}

    def action_validate(self):
        self.validation_time = datetime.date.today()
        self.validation_by = self.env.user
        self.write({"state": "validate"})

    def action_confirm(self):
        self.write({"state": "confirm"})

    @api.model_create_multi
    def create(self, vals_list):
        IrSequence = self.env['ir.sequence']
        for vals in vals_list:
            if not vals.get("name") or vals['name'] == _('New'):
                seq_name = IrSequence.next_by_code('sample.request.seq')
                vals['name'] = seq_name or _('New')
        return super().create(vals_list)