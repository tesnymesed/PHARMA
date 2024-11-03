import datetime

from odoo.exceptions import UserError

from odoo import models, api, fields, _


class SampleRequest(models.Model):
    _name = 'quality.sample.request'
    description = 'Request for a sample'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', copy=False, readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    request_time = fields.Datetime(string="Request Time", tracking=True)
    user_id = fields.Many2one('res.users', string='Requested By', required=True, tracking=True)
    product_id = fields.Many2one('product.product', string='Product', required=True, check_company=True)
    lot_id = fields.Many2one('stock.lot', 'Lot/Serial Number', domain="[('product_id', '=', product_id)]",
                             check_company=True)
    line_ids = fields.One2many('quality.sample.request.lines', 'simple_request_id')
    quality_check_id = fields.Many2one('quality.check', string='Quality Check')
    picking_id = fields.Many2one('stock.picking', string='Picking')
    validation_time = fields.Datetime(string='Validate Time', tracking=True, readonly=True)
    validation_by = fields.Many2one('res.users', string='Validate By', tracking=True, readonly=True)
    location_id = fields.Many2one('stock.location', string='Source Location', required=True)
    type_id = fields.Many2one('stock.picking.type', string='Sample Type', required=True)
    location_dest_id = fields.Many2one('stock.location', string='Destination Location', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('validate', 'Validated'),
        ('rejected', 'Rejected'),
        ('cancel', 'Canceled'),
    ], string='State', default='draft')

    def action_canceled(self):
        self.write({"state": 'cancel'})

    def action_reject(self):
        self.write({"state": 'rejected'})

    def action_confirm(self):
        self.write({"state": "confirm"})

    def action_validate(self):
        self.ensure_one()
        pickings_without_moves = self.filtered(lambda p: not p.line_ids)
        if pickings_without_moves:
            raise UserError(
                _("You can’t validate an empty sample request. Please add some products before proceeding."))
        StockPicking = self.env['stock.picking']
        StockMove = self.env['stock.move']
        StockMoveLine = self.env['stock.move.line']
        picking_type = self.type_id
        location_id = self.location_id
        location_dest_id = self.location_dest_id
        line_ids = self.line_ids
        picking = StockPicking.create({
            'picking_type_id': picking_type.id,
            'sample_request_id': self.id,
            'location_id': location_id.id,
            'location_dest_id': location_dest_id.id,
        })
        self.picking_id=picking.id
        move_vals = []
        move_line_vals = []

        for line in line_ids:
            product_id = line.product_id
            move_vals.append({
                'picking_id': picking.id,
                'product_id': product_id.id,
                'product_uom_qty': line.product_quantity,
                'product_uom': product_id.uom_id.id,
                'location_id': location_id.id,
                'location_dest_id': location_dest_id.id,
                'name': 'sample for ' + str(product_id.name),
            })
        moves = StockMove.create(move_vals)

        for move, line in zip(moves, line_ids):
            move_line_vals.append({
                'move_id': move.id,
                'quantity': line.product_quantity,
                'quant_id': line.lot_id.quant_ids.filtered_domain([
                    ('location_id', '=', location_id.id)
                ]).id, })

        StockMoveLine.create(move_line_vals)
        # picking.action_confirm()
        # picking.button_validate()
        self.validation_time = datetime.date.today()
        self.validation_by = self.env.user
        self.write({"state": "validate"})

    @api.model_create_multi
    def create(self, vals_list):
        IrSequence = self.env['ir.sequence']
        for vals in vals_list:
            if not vals.get("name") or vals['name'] == _('New'):
                seq_name = IrSequence.next_by_code('quality.sample.request.seq')
                vals['name'] = seq_name or _('New')
        return super().create(vals_list)

    def action_quality_check(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Quality check',
            'view_mode': 'form',
            'res_model': 'quality.check',
            'res_id': self.quality_check_id.id or False,
            # 'context': {'simple_request_ids': self.id},
        }

    def action_stock_picking(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock Picking',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            "domain": [('sample_request_id', '=', self.id)],
            'context': {'create': False, },

        }


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sample_request_id = fields.Many2one("quality.sample.request")
