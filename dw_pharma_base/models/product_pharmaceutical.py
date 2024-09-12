# -*- coding:utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError


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
    product_categ_id = fields.Many2one(
        'product.category',
        string='Product Category'
    )
    company_id = fields.Many2one('res.company', string='Company', )
    subfamily_ids = fields.One2many('product.pharmaceutical.subfamily', 'family_id', string='Subfamily')
    product_count = fields.Integer(compute="_compute_product_count")
    product_ids = fields.One2many('product.template', 'dw_pharma_family_id', string='Products')
    purchase_ok = fields.Boolean('Can be Purchased', default=False, track_visibility='onchange')
    sale_ok = fields.Boolean('Can be Sold', default=False, track_visibility='onchange')
    tracking = fields.Selection([
        ('serial', 'By Unique Serial Number'),
        ('lot', 'By Lots'),
        ('none', 'No Tracking')],
        string="Tracking", required=True, default='none', track_visibility='onchange')
    use_expiration_date = fields.Boolean(
        string='Use Expiration Date', track_visibility='onchange')

    def _compute_product_count(self):
        for record in self:
            record.product_count = len(record.mapped('product_ids'))

    def action_view_product(self):
        """
             This method is used by the Product Family smart button. It opens a form view or a tree view
             :return: Action Dict
             """

        product = self.mapped('product_ids')
        if not product:
            raise UserError(
                _('There is no Product to view.')
            )
        tree_view = self.env.ref('dw_pharma_base.product_pharma_family_view_tree')
        form_view = self.env.ref('dw_pharma_base.product_pharma_family_view_form')
        action = {
            'name': _('Purchase Order(s)'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'context': {'default_purchase_order_ids': [(4, self.id)]}
        }
        if len(product) == 1:
            action['views'] = [(form_view.id, 'form')]
            action['res_id'] = product.id
            action['view_mode'] = 'form'
        else:
            action['views'] = [(tree_view.id, 'tree'), (form_view.id, 'form')]
            action['domain'] = [('id', 'in', product.ids)]
        return action


class DwProductPharmaceuticalSubfamily(models.Model):
    _name = 'product.pharmaceutical.subfamily'
    _description = 'Subfamily'

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
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


class DwProductPharmaceuticalNature(models.Model):
    _name = 'product.pharmaceutical.nature'
    _description = 'Nature article'

    name = fields.Char(string="Name")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', )
    description = fields.Text(string="Description")
