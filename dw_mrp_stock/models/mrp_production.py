import datetime

from odoo import fields, api, models, _
from odoo.exceptions import UserError, ValidationError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    dw_transfer_pf_done = fields.Boolean(string='Transfert PF Fait', default=False, tracking=True)
    dw_is_colture = fields.Boolean(string='OF Cloturé', default=False, tracking=True)
    dw_leftover_done = fields.Boolean(string='leftover Done', default=False)

    def _prepare_picking_transfer_pf_datas(self, group_id, location_id, location_dest_id, operation_id):
        lines = []
        product_id = self.product_id
        lines.append([0, 0, {
            'product_id': product_id.id,
            'name': product_id.display_name,
            'product_uom_qty': self.qty_producing,
            'product_uom': self.product_uom_id.id,
            'company_id': self.env.company.id,
            'date': datetime.datetime.now(),
            'location_id': location_id.id,
            'location_dest_id': location_dest_id.id,
            'procure_method': 'make_to_stock',
            'picking_type_id': self.location_src_id.warehouse_id.int_type_id.id,
            'group_id': group_id.id,
            'production_id': False
        }])
        datas = {
            'picking_type_id': operation_id.id,
            'location_id': location_id.id,
            'location_dest_id': location_dest_id.id,
            'move_type': 'direct',
            'origin': self.name,
            'production_id': self.id,
            'move_ids_without_package': lines
        }
        return datas

    def action_create_picking_transfer_pf(self):
        self.ensure_one()
        self.sudo().write({'dw_transfer_pf_done': True})
        StockPicking = self.env['stock.picking'].sudo()
        group_id = self.procurement_group_id
        if not group_id:
            self.env['procurement.group'].sudo().create({
                'name': self.name,
                'move_type': 'direct',
            })

            self.write({
                'procurement_group_id': group_id.id
            })
        location_src_id = self.location_dest_id
        warehouse_id = location_src_id.warehouse_id
        location_transit_id = warehouse_id.dw_transit_production_id
        location_dest_id = warehouse_id.wh_input_stock_loc_id
        in_type_operation = warehouse_id.int_type_id
        if not location_transit_id:
            raise ValidationError(_("There are no transit location selected"))
        data = [self._prepare_picking_transfer_pf_datas(group_id, location_src_id, location_transit_id, in_type_operation)]
        data.append(self._prepare_picking_transfer_pf_datas(group_id, location_transit_id, location_dest_id,in_type_operation))

        datas = data
        picking_ids = StockPicking.create(datas)
        [pick.sudo().action_assign() for pick in picking_ids]
        return {
            'name': _('PF Picking(s)'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('production_id', '=', self.id), ('id', 'in', picking_ids.ids)],
            'context': {'default_production_id': self.id},
        }

    def action_confirm_mp_colture(self):
        if any(not rec.dw_leftover_done for rec in self):
            raise UserError(('Vous ne pouvez pas cloturer sans faire le retour !.'))
        if any(not rec.dw_transfer_pf_done and not rec.mrp_production_source_count for rec in self):
            raise UserError(('Vous ne pouvez pas cloturer sans faire le Transfert du Profuit Fini !.'))
        self.sudo().write({'dw_is_colture': True})
