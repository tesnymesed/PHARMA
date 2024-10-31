from odoo import api, fields, models, _


class DwStockProductionLot(models.Model):
    _inherit = 'stock.lot'

    dw_num_supplier = fields.Char(string="Ref Supplier")


class DwStockLocation(models.Model):
    _inherit = 'stock.location'

    dw_is_quarantine = fields.Boolean(string="Is Quarantine")


class DwStockPicking(models.Model):
    _inherit = 'stock.quant'

    ref = fields.Char(related='lot_id.ref')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        for picking in self:
            res = super(StockPicking, self).button_validate()
            if picking.picking_type_id.code != 'incoming':
                return res
            if not picking.location_dest_id.dw_is_quarantine:
                return res
            warehouse_id = picking.location_dest_id.warehouse_id
            if not warehouse_id or not warehouse_id.dw_quality_operation_id:
                return res
            quality_operation_id = warehouse_id.dw_quality_operation_id
            for move in picking.move_line_ids.filtered(lambda m: m.location_dest_id.dw_is_quarantine):
                quality_picking = picking._create_quality_picking(picking, quality_operation_id)
                quality_move = picking._create_quality_move(quality_picking, move, quality_operation_id)
                picking._create_quality_move_line(quality_move, move, quality_operation_id)
                msg = _("Automatically generated from %(origin)s.", origin=picking.name, )
                quality_picking.message_post(body=msg,
                                             author_id=self.env.ref("base.partner_root").id,)
                quality_picking.action_confirm()
            return res

    def _create_quality_picking(self, picking, quality_operation_id):
        picking_quality = []
        picking_quality.append({
            'picking_type_id': quality_operation_id.id,
            'location_id': picking.location_dest_id.id,
            'location_dest_id': quality_operation_id.default_location_dest_id.id,
            'origin': picking.name,
        })
        if picking_quality:
            return self.env['stock.picking'].create(picking_quality)
        return False

    def _create_quality_move(self, quality_picking, move, quality_operation_id):
        picking_move = []
        picking_move.append({
            'name': move.product_id.name,
            'product_id': move.product_id.id,
            'product_uom_qty': move.quantity,
            'product_uom': move.product_uom_id.id,
            'picking_id': quality_picking.id,
            'location_id': quality_picking.location_id.id,
            'location_dest_id': quality_operation_id.default_location_dest_id.id,
        })
        if picking_move:
            return self.env['stock.move'].create(picking_move)
        return False

    def _create_quality_move_line(self, quality_move, move, quality_operation_id):
        picking_move_line = []
        picking_move_line.append({
            'move_id': quality_move.id,
            'picking_id': quality_move.picking_id.id,
            'product_id': move.product_id.id,
            'lot_id': move.lot_id.id,
            'product_uom_id': move.product_uom_id.id,
            # 'quantity': move.quantity,
            'location_id': quality_move.location_id.id,
            'location_dest_id': quality_operation_id.default_location_dest_id.id,
        })
        if picking_move_line:
            return self.env['stock.move.line'].create(picking_move_line)
        return False
