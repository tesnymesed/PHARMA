import datetime

from odoo import models, api, fields, _
from odoo.exceptions import UserError


class SampleRequest(models.Model):
    _name = 'sample.request'
    description = 'Request for a sample'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', copy=False, readonly=True)
    company_id = fields.Many2one('res.company',string='Company', default=lambda self: self.env.company, required=True)
    request_time = fields.Datetime(string="Request Time", tracking=True)
    user_id= fields.Many2one('res.users',string='Requested By',required=True, tracking=True)
    product_id = fields.Many2one('product.product',string='Product',required=True)
    lot_id = fields.Many2one('stock.lot', 'Lot/Serial Number',domain="[('product_id', '=', product_id)]", check_company=True)
    line_ids = fields.One2many('sample.request.lines','simple_request_id')
    quality_check_id =fields.Many2one('quality.check', string='Quality Check')
    validation_time = fields.Datetime(string='Validate Time', tracking=True, readonly=True)
    validation_by = fields.Many2one('res.users',string='Validate By', tracking=True, readonly=True)
    picking_id = fields.Many2one('stock.picking', string='Picking')
    location_id = fields.Many2one('stock.location',string='Source Location', required=True)
    location_dest_id = fields.Many2one('stock.location',string='Destination Location', required=True)
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

    def action_confirm(self):
        self.write({"state": "confirm"})

    def action_validate(self):
        self.ensure_one()
        for rec in self:
            pickings_without_moves = self.filtered(lambda p: not p.line_ids )
            if pickings_without_moves:
                raise UserError(_("You can’t validate an empty sample request. Please add some products before proceeding."))
            StockPicking = self.env['stock.picking']
            StockMove = self.env['stock.move']
            StockMoveLine = self.env['stock.move.line']
            picking_type = self.env.ref('stock.picking_type_internal')
            picking = StockPicking.create({
                'picking_type_id': picking_type.id,
                'location_id': rec.location_id.id,
                'location_dest_id': rec.location_dest_id.id,
            })
            move_vals = []
            move_line_vals = []

            for line in rec.line_ids:
                move_vals.append({
                    'picking_id': picking.id,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_quantity,
                    'product_uom': line.product_id.uom_id.id,
                    'location_id': rec.location_id.id,
                    'location_dest_id': rec.location_dest_id.id,
                    'name': 'test',
                })
            moves = StockMove.create(move_vals)

            for move, line in zip(moves, rec.line_ids):
                move_line_vals.append({
                    'move_id': move.id,
                    # 'quant_id': line.lot_id.quant_id.id,
                })

            StockMoveLine.create(move_line_vals)
            picking.action_confirm()
            picking.button_validate()
            self.validation_time = datetime.date.today()
            self.validation_by = self.env.user
            self.write({"state": "validate"})


    @api.model_create_multi
    def create(self, vals_list):
        IrSequence = self.env['ir.sequence']
        for vals in vals_list:
            if not vals.get("name") or vals['name'] == _('New'):
                seq_name = IrSequence.next_by_code('sample.request.seq')
                vals['name'] = seq_name or _('New')
        return super().create(vals_list)

    def action_quality_check(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Quality check',
            'view_mode': 'form',
            'res_model': 'quality.check',
            'res_id': self.quality_check_id.id if self.quality_check_id else False,
            'context': {'simple_request_ids': self.id},
        }

    def action_stock_picking(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock Picking',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',

        }