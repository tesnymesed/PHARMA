# -*- coding: utf-8 -*-

from odoo import models


class DwMrpSimulationWorkCenter(models.Model):
    _name = "dw.mrp.simulation.workcenter"
    _inherit = "mrp.workcenter"


class DwMrpWorkCenterClone(models.Model):
    _inherit = "mrp.workcenter"

    def create(self, vals_list):
        records = super().create(vals_list)
        cloned_records = self.env['dw.mrp.simulation.workcenter'].create(vals_list)
        return records
