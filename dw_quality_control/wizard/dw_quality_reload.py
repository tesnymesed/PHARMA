import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class DwQualityReloadLoc(models.Model):
    _name = "dw.quality.reload.location"

    location_id = fields.Many2one("stock.location", required=0, string="Emplacement Source")
    dest_location_id = fields.Many2one("stock.location", string="Emplacement Destination",
                                       compute="compute_dest_location_id")
    quantity = fields.Float("Quantité")
    warehouse_id = fields.Many2one("stock.warehouse", compute="compute_dest_location_id", string="Entrepot")

    @api.depends("location_id")
    def compute_dest_location_id(self):
        for record in self:
            record.dest_location_id = record.location_id.warehouse_id.lot_stock_id if record.location_id else None
            record.warehouse_id = record.location_id.warehouse_id if record.location_id else None


class DwQualityReload(models.TransientModel):
    _name = "dw.quality.reload"

    check_quality_id = fields.Many2one(
        "quality.check"
    )
    lot_id = fields.Many2one(
        "stock.lot"
    )
    location_ids = fields.Many2many("dw.quality.reload.location")
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        check_quality_id = self.env['quality.check'].browse(self.env.context['active_id'])
        res["check_quality_id"] = check_quality_id.id
        lot_id = check_quality_id.lot_id
        res["lot_id"] = lot_id.id
        location_ids = []
        quant_ids = lot_id.quant_ids.filtered(
            lambda l: l.location_id.usage in ['internal'] and l.location_id.dw_is_quarantine)
        for quant in quant_ids:
            if quant.quantity:
                data = [0, 0, {
                    'location_id': quant.location_id.id,
                    'quantity': quant.quantity,

                }]
                location_ids.append(data)

        res["location_ids"] = location_ids
        return res

    def action_reload(self):
        CheckQuality = self.env["quality.check"].sudo()
        check_quality_id = self.check_quality_id
        location_ids = self.location_ids
        picking_id = check_quality_id.picking_id
        product_id = check_quality_id.product_id

        if picking_id:
            if len(location_ids) == 1 and location_ids[-1].location_id.id != picking_id.location_id.id:
                quant = location_ids[-1]
                location_id = quant.location_id
                dest_location_id = quant.dest_location_id
                qty = quant.quantity
                quality_operation_id = quant.warehouse_id.dw_quality_operation_id
                if not quality_operation_id:
                    raise UserError(_("Please select a quality operation for the warehouse : ('%s').", quant.warehouse_id.name))
                lines = []
                lines.append([0, 0, {
                    'product_id': product_id.id,
                    'name': product_id.display_name,
                    'product_uom_qty': qty if qty else 0,
                    'product_uom': product_id.uom_id.id,
                    'company_id': self.env.company.id,
                    'date': datetime.datetime.now(),
                    'location_id': location_id.id,
                    'location_dest_id': dest_location_id.id,
                    'procure_method': 'make_to_stock',
                    'picking_type_id': quality_operation_id.id,
                }])
                if lines:
                    datas = {
                        'picking_type_id': quality_operation_id.id,
                        'location_id': location_id.id,
                        'location_dest_id': dest_location_id.id,
                        'move_type': 'direct',
                        'origin': picking_id.origin if picking_id.origin else check_quality_id.name,
                        'move_ids_without_package': lines
                    }
                    tr_picking_ids = self.env['stock.picking'].sudo().create(datas) if datas else None
                    if tr_picking_ids:
                        tr_picking_ids.sudo().action_assign()
                        line_ids = []
                        id_lot = check_quality_id.lot_id.id
                        for line in tr_picking_ids.move_line_ids_without_package:
                            line_ids.append(
                                (
                                    1, line.id, {'lot_id': id_lot}))
                        tr_picking_ids.sudo().write({"move_line_ids_without_package": line_ids})
                        for check in tr_picking_ids.check_ids:
                            check.check_number = check_quality_id.check_number
                            check.verdict = check_quality_id.verdict
                            check.lot_id = check_quality_id.lot_id.id
                        if tr_picking_ids[0].check_ids :
                            return {
                                'name': 'Quality',
                                'type': 'ir.actions.act_window',
                                'view_mode': 'form',
                                'res_model': 'quality.check',
                                'res_id': tr_picking_ids[0].check_ids[0].id,
                                'domain': [('id', 'in', tr_picking_ids.check_ids.ids if tr_picking_ids.check_ids else [])],
                            }

                # picking_id.sudo().action_assign()
            elif len(location_ids) != 1:
                quant_location_ids = self.location_ids
                p_id = picking_id.location_id.id
                product_id = check_quality_id.product_id
                id_lot = check_quality_id.lot_id

                data_list = []
                for quant in quant_location_ids:
                    if quant.location_id.id != p_id:
                        location_id = quant.location_id
                        check_to_assign = CheckQuality.search(
                            [("lot_id.id", '=', id_lot.id), ('picking_id.location_id.id', '=', location_id.id),
                             ("company_id", '=', self.company_id.id)], limit=1)
                        if not check_to_assign:
                            dest_location_id = quant.dest_location_id
                            qty = quant.quantity
                            quality_operation_id = quant.warehouse_id.dw_quality_operation_id
                            lines = []
                            lines.append([0, 0, {
                                'product_id': product_id.id,
                                'name': product_id.display_name,
                                'product_uom_qty': qty if qty else 0,
                                'product_uom': product_id.uom_id.id,
                                'company_id': self.env.company.id,
                                'date': datetime.datetime.now(),
                                'location_id': location_id.id,
                                'location_dest_id': dest_location_id.id,
                                'procure_method': 'make_to_stock',
                                'picking_type_id': quality_operation_id.id,
                            }])
                            if lines:
                                datas = {
                                    'picking_type_id': quality_operation_id.id,
                                    'location_id': location_id.id,
                                    'location_dest_id': dest_location_id.id,
                                    'move_type': 'direct',
                                    'origin': picking_id.origin if picking_id.origin else check_quality_id.name,
                                    'move_ids_without_package': lines
                                }
                                data_list.append(datas)
                        else:
                            check_to_assign.sudo().write({"dw_quality_id": check_quality_id.id})

                    else:
                        line_ids = []
                        for line in picking_id.move_ids_without_package:
                            line_ids.append(
                                (
                                    1, line.id, {'product_uom_qty': quant.quantity}))
                        picking_id.sudo().write({"move_ids_without_package": line_ids})
                        line_ids = []
                        for line in picking_id.move_line_ids_without_package:
                            line_ids.append(
                                (
                                    1, line.id, {'lot_id': id_lot.id}))
                        picking_id.sudo().write({"move_line_ids_without_package": line_ids})
                        # picking_id.sudo().action_assign()

                tr_picking_ids = self.env['stock.picking'].sudo().create(data_list) if data_list else None
                if tr_picking_ids:
                    for picking in tr_picking_ids:
                        picking.sudo().action_assign()
                        line_ids = []
                        id_lot = check_quality_id.lot_id.id
                        for line in picking.move_line_ids_without_package:
                            line_ids.append(
                                (
                                    1, line.id, {'lot_id': id_lot}))
                        picking.sudo().write({"move_line_ids_without_package": line_ids})

                    check_ids = tr_picking_ids.mapped("check_ids")
                    if check_quality_id.dw_check_ids:
                        check_quality_id.dw_check_ids.mapped('picking_id').sudo().unlink()
                    for check in check_ids:
                        check.sudo().write({"dw_quality_id": check_quality_id.id})
