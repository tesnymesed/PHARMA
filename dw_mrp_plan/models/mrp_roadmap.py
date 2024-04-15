import datetime
import math
from re import findall, split

from odoo import _, fields, models, api
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    roadmap_id = fields.Many2one(
        'mrp.roadmap'
    )


class MrpRoadmap(models.Model):
    _name = 'mrp.roadmap'

    name = fields.Char(
        readonly=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ],
        default='draft')
    date = fields.Date(
        default=datetime.date.today(),
    )
    production_ids = fields.One2many(
        'mrp.production',
        'roadmap_id',
    )
    mrp_line_plan_id = fields.Many2one(
        'product.mrp.plan',
        readonly=True,
    )
    product_id = fields.Many2one(
        'product.product',
        readonly=True,
    )
    uom_id = fields.Many2one(
        'uom.uom',
        related='product_id.uom_id',
        readonly=True,
    )

    default_code = fields.Char(
        related='product_id.default_code',
    )

    lot_ids = fields.Many2many(
        'stock.lot',
        readonly=True,
    )
    quantity = fields.Float(
        readonly=True,
    )
    quantity_per_lot = fields.Float(
        readonly=True,
    )
    bom_id = fields.Many2one(
        'mrp.bom',
        'BoM',
        readonly=True,
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.user.company_id,
    )
    first_lot = fields.Char(
    )
    additional_quantity = fields.Float(
        compute='_compute_quantity'
    )

    production_ratio = fields.Float(
        compute='_compute_production_ratio'
    )

    mrp_line_weekly_plan_id = fields.Many2one(
        'product.mrp.plan.weekly',
        readonly=True,
    )

    @api.depends('quantity', 'production_ids.state', 'production_ids.qty_producing')
    def _compute_production_ratio(self):
        for record in self:
            if record.quantity:
                done_mo = record.production_ids.filtered(
                    lambda p: p.state == 'done' and p.product_id == record.product_id)
                record.production_ratio = sum(done_mo.mapped('qty_producing')) / record.quantity * 100
            else:
                record.production_ratio = 0.0

    @api.depends("lot_ids")
    def _compute_quantity(self):
        for record in self:
            qty = (len(record.lot_ids) * record.quantity_per_lot) - record.quantity
            record.additional_quantity = qty if qty >= 0 else 0

    def action_view_productions(self):

        action = self.env["ir.actions.actions"]._for_xml_id("mrp.mrp_production_action")
        action['domain'] = [('roadmap_id', '=', self.id)]
        action['context'] = {'default_roadmap_id': self.id}

        return action

    def _generate_serial_numbers(self, next_serial_count):
        self.ensure_one()

        first_lot = self.first_lot
        caught_initial_number = findall("\d+", first_lot)
        if not caught_initial_number:
            raise UserError(_('The serial number must contain at least one digit.'))

        initial_number = int(caught_initial_number[-1])
        padding = len(str(initial_number))
        splitted = split(str(initial_number), first_lot)
        prefix, suffix = ''.join(splitted[:-1]), splitted[-1]

        lot_names = []
        for i in range(next_serial_count):
            lot_names.append(f'{prefix}{str(initial_number + i).zfill(padding)}{suffix}')

        if self.lot_ids and lot_names[-1] in self.lot_ids.mapped('name'):
            return self._generate_serial_numbers(next_serial_count=next_serial_count + 1)

        return lot_names[-1] if lot_names else first_lot

    def next_lot(self):

        res = self.env['stock.lot'].create({
            'product_id': self.product_id.id,
            'company_id': self.company_id.id,
            'name': self._generate_serial_numbers(
                next_serial_count=len(self.lot_ids)
            ),
        })

        self.lot_ids = [(4, res.id)]
        return res

    def _prepare_mrp_production_data(self, lot_producing_id):
        return {
            'product_id': self.product_id.id,
            'product_qty': self.quantity_per_lot,
            'bom_id': self.bom_id.id,
            'roadmap_id': self.id,
            'product_uom_id': self.uom_id.id,
            'lot_producing_id': lot_producing_id.id,
        }

    def _prepare_move_line_data(self, production):
        return {
            'name': production.name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.quantity_per_lot,
            'product_uom': self.uom_id.id,
            'picking_type_id': production.picking_type_id.id,
            'location_id': 5,  # virtual location / production
            'location_dest_id': production.picking_type_id.default_location_dest_id.id,
            'company_id': self.company_id.id,
            'warehouse_id': production.picking_type_id.warehouse_id.id,
            'origin': production.name,
            'group_id': production.procurement_group_id.id,
            'state': 'draft',
            'product_uom_category_id': self.product_id.uom_id.category_id.id
        }

    def create_mrp_production(self, lot_count=0):
        datas = []

        additional_quantity = self.env.context.get("additional_quantity", False)
        lot_count = 1 if additional_quantity else math.ceil(self.quantity / self.quantity_per_lot)

        existing_productions = self.production_ids.filtered(lambda l: l.state != 'cancel')
        if lot_count <= len(existing_productions) and not additional_quantity:
            raise UserError(_("The requested quantity is already satisfied by the existing MO(s)"))
        i = 0
        for i in range(lot_count):
            lot_producing_id = self.next_lot()
            data = self._prepare_mrp_production_data(lot_producing_id)
            datas.append(data)

        productions = self.env['mrp.production'].create(datas)

        # move_lines = [self._prepare_move_line_data(production) for production in productions]

        # productions.write({
        #     'move_finished_ids': [(0, 0, move_line) for move_line in move_lines],
            # 'location_src_id': productions.mapped('picking_type_id.default_location_src_id.id'),
            # 'location_dest_id': productions.mapped('picking_type_id.default_location_dest_id.id'),
        # })

        productions._compute_move_raw_ids()
        self.action_mark_as_done()

        return productions

    def action_mark_as_done(self):
        self.write({
            "state": 'done'
        })

    def action_cancel(self):
        if self.production_ids:
            raise UserError(_("You cannot cancel a roadmap with existing OF (s)"))
        self.write({
            "state": 'cancel'
        })

    @api.model
    def create(self, values):
        if not values.get('name'):
            sequence_id = int(self.env['ir.config_parameter'].sudo().get_param('dw_mrp_roadmap_sequence_id'))
            sequence = self.env['ir.sequence'].browse(sequence_id)
            values['name'] = sequence.next_by_id() if sequence else "New"
        return super(MrpRoadmap, self).create(values)