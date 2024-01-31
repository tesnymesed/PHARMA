# -*- coding:utf-8 -*-

from odoo import fields, models


class DwProductPharmaceuticalDosage(models.Model):
    _name = 'product.pharmaceutical.dosage'
    _description = 'Dosage'

    name = fields.Char(string="Name")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', )


class DwProductPharmaceuticalFamily(models.Model):
    _name = 'product.pharmaceutical.family'
    _description = 'Family'
    _inherit = ['mail.thread.main.attachment', 'mail.activity.mixin']

    name = fields.Char(string="Name")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', )
    subfamily_ids = fields.One2many('product.pharmaceutical.subfamily', 'family_id', string='Subfamily')


class DwProductPharmaceuticalSubfamily(models.Model):
    _name = 'product.pharmaceutical.subfamily'
    _description = 'Subfamily'

    name = fields.Char(string="Name")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', )
    family_id = fields.Many2one('product.pharmaceutical.family', string='Family')


class DwProductPharmaceuticalClass(models.Model):
    _name = 'product.pharmaceutical.class'
    _description = 'Class'
    _inherit = ['mail.thread.main.attachment', 'mail.activity.mixin']

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', )
    subclass_ids = fields.One2many('product.pharmaceutical.subclass', 'class_id', string='Subclass')


class DwProductPharmaceuticalSubclass(models.Model):
    _name = 'product.pharmaceutical.subclass'
    _description = 'Subclass'

    name = fields.Char(string="Name")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', )
    class_id = fields.Many2one('product.pharmaceutical.class', string='Class')


class DwProductPharmaceuticalForm(models.Model):
    _name = 'product.pharmaceutical.form'
    _description = 'Form'
    _inherit = ['mail.thread.main.attachment', 'mail.activity.mixin']

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', )
    subform_ids = fields.One2many('product.pharmaceutical.subform', 'form_id', string='Subform')


class DwProductPharmaceuticalSubform(models.Model):
    _name = 'product.pharmaceutical.subform'
    _description = 'Subform'

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', )
    form_id = fields.Many2one('product.pharmaceutical.form', string='Form')


class DwProductPharmaceuticalNetwork(models.Model):
    _name = 'product.pharmaceutical.network'
    _description = 'Network'

    name = fields.Char(string="Name")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', )
    description = fields.Text(string="Description")


class DwProductPharmaceuticalPfDest(models.Model):
    _name = 'product.pharmaceutical.pf.dest'
    _description = 'PF destination'

    name = fields.Char(string="Name")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', )
    description = fields.Text(string="Description")
