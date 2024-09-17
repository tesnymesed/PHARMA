from odoo import fields, api, models, _


class DwMrpForm(models.Model):
    _name = 'dw.mrp.bom.form'

    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', )