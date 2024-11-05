# -*- coding:utf-8 -*-

from odoo import fields, models


class DwResPartner(models.Model):
    _inherit = 'res.partner'

    dw_supplier_nature = fields.Selection(
        [('fabricant', 'Fabricant'), ('regroupeur', 'Regroupeur'),('distributeur_exclusif','distributeur_exclusif'),('Distributeur','Distributeur')],
        string="Supplier nature",
    )
