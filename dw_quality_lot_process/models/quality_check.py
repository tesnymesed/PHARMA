from odoo import models, fields, api, _


class QualityCheck(models.Model):
    _inherit = "quality.check"

    check_lot_compliance = fields.Boolean(related='product_id.requires_lot_compliance_check')
    initial_qty = fields.Float(string="Initial Quanity", readonly=True)

    

    def _set_initial_qty(self):
        self.initial_qty =self.picking_lot_quantity
        self.lot_id.initial_qty = self.picking_lot_quantity
    
    def do_pass(self):
        if self.lot_id and self.lot_id.compliance_check:
            if self.lot_id.lot_quarantine_status != 'analyzed':
                self.lot_id.action_set_analyzed()
            self.lot_id.action_set_conform()
        self._set_initial_qty()
        return super().do_pass()

    def do_fail(self):
        self._set_initial_qty()
        return super().do_fail()

    def do_fail_process(self):

        if self.lot_id and self.lot_id.compliance_check:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Cancel Lot',
                'res_model': 'stock.lot.cancel.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_lot_id': self.lot_id.id, 'default_check_quality_id': self.id}
            }
    def do_pass_process(self):
        if self.lot_id and self.lot_id.compliance_check:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Sub Lot REgister',
                'res_model': 'stock.lot.sub.lot.register',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_lot_id': self.lot_id.id, 'default_check_quality_id': self.id}
            }