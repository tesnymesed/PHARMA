from odoo import models, fields, _


class DwMrpProductionTargets(models.Model):
    _name = 'dw.mrp.production.target'
    _description = 'MRP Yearly Production Targets'

    name = fields.Char('Ref', copy=False, required=True, default=_('New'))

    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', readonly=True)

    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)

    product_target_ids = fields.One2many('dw.mrp.product.target', 'target_id', string="Target Lines")


    def action_mrp_target(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'name': _('Target Plan'),
            'tag': 'mrp_target_plan',
            'context': {'res_id': self.id}
        }

    def action_approve(self):
        self.state = 'approved'
        for line in self.product_target_ids:
            line.action_approve()

    def action_reject(self):
        self.state = 'rejected'
        for line in self.product_target_ids:
            line.action_reject()

    def action_done(self):
        self.state = 'done'
        for line in self.product_target_ids:
            line.action_done()

    def action_cancel(self):
        self.state = 'cancelled'
        for line in self.product_target_ids:
            line.action_cancel()

    def unlink(self):
        for record in self:
            for target_line in record.product_target_ids:
                target_line.unlink()
        return super().unlink()
