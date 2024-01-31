# -*- coding:utf-8 -*-

from odoo import fields, models


class DwProductTemplate(models.Model):
    _inherit = 'product.template'

    dw_pharma_dci = fields.Char(string="DCI")
    dw_pharma_regis_num = fields.Char(string="Registration Number")
    dw_pharma_date_de = fields.Date(string="Date DE")
    dw_pharma_dosage_id = fields.Many2one('product.pharmaceutical.dosage', string="Dosage")
    dw_pharma_family_id = fields.Many2one('product.pharmaceutical.family', string='Family')
    dw_pharma_subfamily_id = fields.Many2one('product.pharmaceutical.subfamily', string='Subfamily')
    dw_pharma_class_id = fields.Many2one('product.pharmaceutical.class', string='Class')
    dw_pharma_subclass_id = fields.Many2one('product.pharmaceutical.subclass', string='Subclass')
    dw_pharma_form_id = fields.Many2one('product.pharmaceutical.form', string="Form")
    dw_pharma_subform_id = fields.Many2one('product.pharmaceutical.subform', string="Subform")
    dw_pharma_network_id = fields.Many2one('product.pharmaceutical.network', string="Network")
    dw_pharma_pf_dest_id = fields.Many2one('product.pharmaceutical.pf.dest', string="PF Destination")
