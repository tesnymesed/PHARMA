from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError


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
    lot_domain = fields.Many2many(
        'stock.lot',
        compute='_compute_lot_domain')

    line_ids = fields.One2many(
        'quality.check.line',
        'quality_check_id',
        store=True,
        compute='_compute_quality_check_line_ids',
        readonly=False
    )
    verdict = fields.Selection([
        ('improper', 'Improper'),
        ('proper', 'Proper')
    ])
    partner_supplier_id = fields.Many2one(
        'res.partner',
        string="Supplier"
        # compute = '_compute_partner_supplier_id'
    )
    manufacturing_date = fields.Datetime(
        compute="_compute_manufacturing_date"
    )
    check_number = fields.Char()
    dw_quality_id = fields.Many2one('quality.check', string="Quality Parent")
    dw_reception_id = fields.Many2one('stock.picking', string="Reception")
    dw_purchase_id = fields.Many2one('purchase.order', string="Purchase")
    location_id = fields.Many2one(
        'stock.location',
        compute='_compute_per_picking_id_lot_id'
    )
    picking_lot_quantity = fields.Float(
        compute='_compute_per_picking_id_lot_id', string="Quantity Lot"
    )
    count_dw_check_ids = fields.Float(
        compute='_compute_count_dw_check_ids'
    )
    dw_check_ids = fields.One2many(
        'quality.check', "dw_quality_id"
    )
    lot_domain_reception = fields.Many2many('stock.lot', 'rel_lot_quality', 'quality_id', 'lot_id',
                                            string='lots', compute="compute_lot_domain_reception", store=1, readonly=0)
    dw_route_no_origin = fields.Boolean(default=False, related="picking_id.dw_route_no_origin")
    simple_request_ids = fields.Many2one('sample.request', string='Simple Request')

    @api.depends('dw_check_ids')
    def _compute_count_dw_check_ids(self):
        for record in self:
            record.count_dw_check_ids = len(record.dw_check_ids)

    @api.depends('lot_id', 'finished_lot_id', 'picking_id', 'production_id')
    def _compute_per_picking_id_lot_id(self):
        for record in self:
            if record.lot_id and record.picking_id:

                location_id = record.picking_id.location_id.id
                record.location_id = location_id
                record.picking_lot_quantity = sum(record.lot_id.quant_ids.filtered(
                    lambda l: l.location_id.id == location_id).mapped("quantity"))
            elif record.production_id and record.finished_lot_id:
                location_id = record.production_id.location_src_id.id
                record.location_id = location_id
                record.picking_lot_quantity = sum(record.finished_lot_id.quant_ids.filtered(
                    lambda l: l.location_id.id == location_id).mapped("quantity"))
            else:
                record.location_id = False
                record.picking_lot_quantity = 0

    @api.depends('production_id')
    def _compute_manufacturing_date(self):
        for record in self:
            record.manufacturing_date = record.production_id.date_finished

    # @api.onchange('picking_id')
    # def _compute_partner_supplier_id(self):
    #     PurchaseOrder = self.env["purchase.order"].sudo()
    #     StockPicking = self.env["stock.picking"].sudo()
    #
    #     for record in self:
    #         picking_id = record.picking_id
    #         partner_id = picking_id.group_id.partner_id
    #         purchase_picking_id = False
    #         purchase_id = reception_id = False
    #         if picking_id and picking_id.origin:
    #             purchase = True if picking_id.origin.startswith('BC') else False
    #             if purchase:
    #                 purchase_id = PurchaseOrder.search(
    #                     [("name", "=", picking_id.origin), ("company_id", '=', self.company_id.id)], limit=1)
    #                 if purchase_id:
    #                     purchase_picking_id = purchase_id.picking_ids[0] if purchase_id.picking_ids[0] else False
    #                     partner_id = purchase_id.partner_id if not partner_id else partner_id
    #             else:
    #                 reception_id = StockPicking.search(
    #                     [("name", "=", picking_id.origin), ("company_id", '=', self.company_id.id)], limit=1)
    #                 if reception_id:
    #                     purchase_id = reception_id.purchase_id
    #                     purchase_picking_id = reception_id
    #                     partner_id = purchase_id.partner_id if not partner_id else partner_id
    #
    #         record.partner_supplier_id = partner_id
    #         record.dw_reception_id = purchase_picking_id
    #         record.dw_purchase_id = purchase_id

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

    @api.depends('picking_id', "picking_lot_quantity")
    def _compute_lot_domain(self):
        # PurchaseOrder = self.env["purchase.order"].sudo()
        # StockPicking = self.env["stock.picking"].sudo()
        for record in self:
            picking_id = record.picking_id
            lot_ids = picking_id.move_line_ids.mapped('lot_id') if picking_id.move_line_ids else picking_id.move_line_ids_without_package.mapped('lot_id')
            # if not lot_ids:
            #     if not picking_id.production_id and picking_id.origin:
            #         purchase = True if picking_id.origin.startswith('BC') else False
            #         if purchase:
            #             purchase_id = PurchaseOrder.search(
            #                 [("name", "=", picking_id.origin), ("company_id", '=', self.company_id.id)])
            #             purchase_picking_id = purchase_id.picking_ids[0] if purchase_id.picking_ids else None
            #             if purchase_picking_id:
            #                 lot_ids = purchase_picking_id.move_line_ids.mapped(
            #                     'lot_id') if picking_id.move_line_ids else picking_id.move_line_ids_without_package.mapped(
            #                     'lot_id')
            #             else:
            #                 lot_ids = []
            #         else:
            #             picking_tr_id = StockPicking.search(
            #                 [("name", "=", picking_id.origin), ("company_id", '=', self.company_id.id)])
            #             if picking_tr_id:
            #                 lot_ids = picking_tr_id.move_line_ids.mapped(
            #                     'lot_id') if picking_id.move_line_ids else picking_id.move_line_ids_without_package.mapped(
            #                     'lot_id')
            #             else:
            #                 lot_ids = []

            if not lot_ids:
                lot_ids = record.product_id.mapped("stock_quant_ids").mapped("lot_id")

            record.lot_domain = lot_ids

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

    @api.depends('picking_id', 'picking_id.move_line_ids', 'picking_id.move_line_ids_without_package')
    def compute_lot_domain_reception(self):
        for record in self:
            picking_id = record.picking_id
            lot_ids = picking_id.move_line_ids.mapped(
                'lot_id') if picking_id.move_line_ids else picking_id.move_line_ids_without_package.mapped(
                'lot_id')

            record.lot_domain_reception = lot_ids

    def do_fail(self):
        if self.verdict != 'improper':
            raise UserError(_("You can't fail this control without an improper verdict"))
        if self.dw_check_ids:
            for quality in self.dw_check_ids:
                quality.check_number = self.check_number
                quality.verdict = self.verdict
                quality.do_fail()
        return super().do_fail()

    """ def do_pass(self):
        return self.action_lot_approval() """

    def do_pass_per_quality(self):
        if self.verdict != 'proper':
            raise UserError(_("You can't succeed this control without a proper verdict"))

        self.write({'quality_state': 'pass',
                    'user_id': self.env.user.id,
                    'control_date': datetime.now()})
        if self.check_number and self.lot_id:
            self.lot_id.sudo().write({'ref': self.check_number})
        if self.picking_id:
            move_line_ids_without_package = self.sudo().picking_id.move_line_ids_without_package
            # self.picking_id.sudo().action_assign()

            if move_line_ids_without_package:
                line_ids = move_line_ids_without_package.sudo().filtered(
                    lambda line: line.lot_id.id == self.lot_id.id and self.lot_id)
            else:
                line_ids = self.sudo().picking_id.move_line_ids.filtered(
                    lambda line: line.product_id.id == self.product_id.id and self.product_id)

            if line_ids:
                for line in line_ids:
                    line.quantity = line.quantity
            else:
                line_ids.sudo().create({
                    'product_id': self.product_id.id,
                    'product_uom_id': self.picking_id.move_ids_without_package.filtered(lambda o: o if o.product_id == self.product_id else None).product_uom.id,
                    'location_id': self.picking_id.location_id.id,
                    'location_dest_id': self.picking_id.location_dest_id.id,
                    'lot_id': self.lot_id.id,
                    'quantity_product_uom': self.picking_id.move_ids_without_package.filtered(lambda o: o if o.product_id == self.product_id else None).product_uom_qty,
                    'qty_done': self.picking_id.move_ids_without_package.filtered(lambda o: o if o.product_id == self.product_id else None).product_uom_qty,
                    'move_id': self.picking_id.move_ids_without_package.filtered(lambda o: o if o.product_id == self.product_id else None).id,
                    'picking_id': self.picking_id.id
                })
            self.sudo().picking_id.with_context(skip_backorder=True, skip_expired=True).button_validate()
        if self.env.context.get('no_redirect'):
            return True
        return True

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

    def action_reload(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Action Reload',
            'res_model': 'dw.quality.reload',
            'views': [[self.env.ref('dw_quality_control.dw_quality_reload_wizard_form').id, 'form']],
            'target': 'new',
            'view_mode': 'form',

        }

    def action_lot_approval(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Action Lot Approval',
            'res_model': 'dw.quality.lot.approval',
            'view_id': self.env.ref('dw_quality_control.dw_quality_lot_approval_form_wizard').id,
            'target': 'new',
            'view_mode': 'form',
        }

    def action_open_extra_check_ids(self):

        return {
            'name': 'Extra Check Quality',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'quality.check',
            'domain': [('id', 'in', self.dw_check_ids.ids if self.dw_check_ids else [])],
        }

    @api.model
    def create(self, vals_list):
        res = super().create(vals_list)
        if res['picking_id']:
            res['picking_id'].dw_picking_to_merge = True
        return res

    def dw_recompute_state(self):
        self.ensure_one()
        picking_id = self.picking_id
        if picking_id:
            picking_id.dw_recompute_state()

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