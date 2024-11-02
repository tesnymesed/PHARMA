from odoo import models, fields, api


class QualityCheck(models.Model):
    _inherit = "quality.check"

    dw_num_supplier = fields.Char(related="lot_id.dw_num_supplier", store=1)
    use_expiration_date = fields.Boolean(related="lot_id.use_expiration_date", store=1)
    expiration_date = fields.Datetime(related="lot_id.expiration_date", store=1)
    lot_id = fields.Many2one(compute="compute_lot_id", store=1, readonly=0)
    final_product = fields.Boolean()
    raw_material = fields.Boolean()
    product_tracking = fields.Selection([
        ('serial', 'Serial'),
        ('lot', 'Lot'),
        ('none', 'None'),
    ],
        related='product_id.product_tmpl_id.tracking'
    )
    lot_domain = fields.Many2many('stock.lot', compute='_compute_lot_domain')
    line_ids = fields.One2many(
        'quality.check.line',
        'quality_check_id',
        store=True,
        compute='_compute_quality_check_line_ids',
        readonly=False
    )
    partner_supplier_id = fields.Many2one('res.partner', string="Supplier")
    manufacturing_date = fields.Datetime(compute="_compute_manufacturing_date")
    check_number = fields.Char(string='Check Number')
    dw_quality_id = fields.Many2one('quality.check', string="Quality Parent")
    dw_reception_id = fields.Many2one('stock.picking', string="Reception")
    dw_purchase_id = fields.Many2one('purchase.order', string="Purchase")
    location_id = fields.Many2one('stock.location', compute='_compute_per_picking_id_lot_id')
    picking_lot_quantity = fields.Float(compute='_compute_per_picking_id_lot_id', string="Quantity Lot")
    dw_check_ids = fields.One2many('quality.check', "dw_quality_id")
    lot_domain_reception = fields.Many2many('stock.lot', 'rel_lot_quality', 'quality_id', 'lot_id',
                                            string='lots', compute="compute_lot_domain_reception", store=1, readonly=0)

    @api.depends('lot_id', 'picking_id')
    def _compute_per_picking_id_lot_id(self):
        for record in self:
            if record.lot_id and record.picking_id:
                location_id = record.picking_id.location_id.id
                record.location_id = location_id
                record.picking_lot_quantity = sum(record.lot_id.quant_ids.filtered(
                    lambda l: l.location_id.id == location_id).mapped("quantity"))
            # elif record.production_id and record.finished_lot_id:
            #     location_id = record.production_id.location_src_id.id
            #     record.location_id = location_id
            #     record.picking_lot_quantity = sum(record.finished_lot_id.quant_ids.filtered(
            #         lambda l: l.location_id.id == location_id).mapped("quantity"))
            else:
                record.location_id = False
                record.picking_lot_quantity = 0

    @api.depends('product_id')
    def _compute_quality_check_line_ids(self):
        for record in self:
            datas = []
            product_model_ids = record.product_id.quality_model_id.model_ids
            for line in product_model_ids:
                datas.append((0, 0, {
                    'name': line.name,
                    'reference': line.reference,
                    'standards': line.standards,
                    'result': line.result,
                }))
            record.line_ids = datas

    # The lot domain functions will be adjusted soon
    @api.depends('picking_id', "picking_lot_quantity")
    def _compute_lot_domain(self):
        for record in self:
            picking_id = record.picking_id
            lot_ids = picking_id.move_line_ids.mapped(
                'lot_id') if picking_id.move_line_ids else picking_id.move_line_ids_without_package.mapped('lot_id')
            if not lot_ids:
                lot_ids = record.product_id.mapped("stock_quant_ids").mapped("lot_id")
            record.lot_domain = lot_ids

    # The lot domain functions will be adjusted soon
    @api.depends('lot_domain', 'lot_domain_reception')
    def compute_lot_id(self):
        for record in self:
            picking_id = record.picking_id
            lot_ids = False if not picking_id else picking_id.move_line_ids.mapped(
                'lot_id') if picking_id.move_line_ids else picking_id.move_line_ids_without_package.mapped(
                'lot_id')
            if lot_ids and not record.lot_id:
                lot_id = lot_ids[-1].id
            elif record.lot_id:
                lot_id = record.lot_id.id
            else:
                lot_id = False
            record.lot_id = lot_id

    # The lot domain functions will be adjusted soon
    @api.depends('picking_id', 'picking_id.move_line_ids', 'picking_id.move_line_ids_without_package')
    def compute_lot_domain_reception(self):
        for record in self:
            picking_id = record.picking_id
            lot_ids = picking_id.move_line_ids.mapped(
                'lot_id') if picking_id.move_line_ids else picking_id.move_line_ids_without_package.mapped(
                'lot_id')

            record.lot_domain_reception = lot_ids

    # The lot domain functions will be adjusted soon
    @api.onchange('picking_id')
    def onchange_picking_id(self):
        domain = []
        lot_ids = self.picking_id.move_line_ids.mapped(
            'lot_id') if self.picking_id.move_line_ids else self.picking_id.move_line_ids_without_package.mapped(
            'lot_id')
        if lot_ids:
            domain.append(('id', 'in', lot_ids.ids))
        else:
            domain.append(
                ('id', 'in', self.env['stock.lot'].search(
                    [('product_id', '=', self.product_id.id), ("company_id", '=', self.company_id.id)]).ids))
        return {
            'domain': {
                'lot_id': domain
            }
        }


    def button_sample_request(self):
        self.ensure_one()
        line_ids_data = [
            (0, 0, {'product_id': self.product_id.id, 'lot_id':self.lot_id.id,})

        ]
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sample Request',
            'view_mode': 'form',
            'res_model': 'sample.request',
            'res_id': self.simple_request_ids.id if self.simple_request_ids else False,
            'context': {'default_quality_check_id': self.id,
                        'default_location_id':self.location_id.id,
                        'default_product_id':self.product_id.id,
                        'default_user_id':self.user_id.id,
                        'default_lot_id':self.lot_id.id,
                        'default_line_ids': line_ids_data
                        },}

    def action_sample_request(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sample Request',
            'view_mode': 'tree',
            'res_model': 'sample.request',
            "domain": [('quality_check_id', '=', self.id)],
            'context': {'default_quality_check_id': self.id},
        }
