from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class QualityCheck(models.Model):
    _inherit = "quality.check"

    def create(self, vals):
        """override create method and make its status to quarantine and its analyse status to in progress"""
        res = super(QualityCheck, self).create(vals)
        if res.lot_id and res.lot_id.compiliance_check:
            res.lot_id.lot_status ='quarantine'
            res.lot_id.lot_quarantine_status ='in_progress'
        return res
    
    def do_pass(self):
        if self.lot_id and self.lot_id.compiliance_check :
            self.lot_id.lot_quarantine_status='analyzed'
            self.lot_id.lot_status = 'conform'
        return super().do_pass()
    
    def do_fail(self):
        if self.lot_id and self.lot_id.compiliance_check :
            self.lot_id.lot_quarantine_status='analyzed'
            self.lot_id.lot_status = 'not_conform'
            return super().do_fail()
        


