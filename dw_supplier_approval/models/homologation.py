# -*- coding:utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class DwHomologation(models.Model):
    _name = 'dw.homologation'
    _description = "supplier approval"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "start_date desc"

    name = fields.Char(string='Name', default=lambda self: _('New'), copy=False)

    state = fields.Selection(
        selection=[
            ('prospection', 'Prospection'),
            ('analyse', 'Analyse'),
            ('audit', 'Audit'),
            ('rejected', 'Rejected'),
            ('lot_validation', 'Lot Validation'),
            ('qualification', 'Qualification'),
            ('homologue', 'approved'),
            ('cancel', 'Canceled')
        ],
        string="State",
        default="prospection",
        group_expand='_expand_states'
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
    )
    market_id = fields.Many2one('dw.market', string='Market')
    product_id = fields.Many2one(
        'product.product',
        check_company=True,
        compute="_compute_product", readonly=False, store=True, required="1",
        domain=['|', '|', ('homologue', '=', True), ('categ_id.homologue', '=', True),
                ('product_tmpl_id.homologue', '=', True), ('purchase_ok', '=', True)],
    )
    lot_validation = fields.Boolean('Lot Validation')
    supplier_id = fields.Many2one(
        'res.partner', required=1,
        domain='[("is_supplier","=", True)]'
    )
    dw_supplier_nature = fields.Selection(
        [('fabricant', 'Fabricant'), ('regroupeur', 'Regroupeur')],
        string="Supplier nature", related="supplier_id.dw_supplier_nature", readonly=False, store=True,
    )
    product_ids = fields.Many2many(
        'product.product',
    )
    start_date = fields.Date(string="Start Date", default=fields.Date.today)
    end_date = fields.Date(string="End Date", default=fields.Date.today)
    market_supplier_ids = fields.Many2many('res.partner', store="1"
                                           )
    state_market = fields.Selection(

        related="market_id.state"
    )

    email = fields.Char('Email', related="supplier_id.email", readonly=False)

    phone = fields.Char('Phone', related="supplier_id.phone", readonly=False)
    # address fields
    street = fields.Char(string="Address", related="supplier_id.street", readonly=False)
    street2 = fields.Char(related="supplier_id.street", readonly=False)
    zip = fields.Char(related="supplier_id.zip", readonly=False)
    city = fields.Char(related="supplier_id.city", readonly=False)
    state_id = fields.Many2one("res.country.state", string='State', domain="[('country_id', '=?', country_id)]",
                               related="supplier_id.state_id", readonly=False)
    country_id = fields.Many2one('res.country', string='Country', related="supplier_id.country_id", readonly=False)
    country_code = fields.Char(related='country_id.code', string="Country Code", readonly=False)

    purchase_id = fields.Many2one("purchase.order", string="Purchase Order", )
    consultation_id = fields.Many2one("dw.consultation", string="Consultation")

    fichier_stabilite_attachment = fields.Binary(string="Fichier de stabilité")
    fichier_stabilite_file_name = fields.Char(string='File name')
    qty = fields.Float("Quantity")

    @api.constrains('end_date', 'start_date')
    def _check_date_start_end(self):
      for record in self:
        if record.start_date and record.end_date:

            if record.start_date > record.end_date:
                raise ValidationError(
                    _('start date can\'t be greater that end date'))
    def _expand_states(self, states, domain, order):
        return [key for key, dummy in self._fields['state'].selection]

    # @api.depends('market_id')
    # def _compute_market_supplier_ids(self):
    #     for record in self :
    #         record.market_supplier_ids = record.market_id.market_line_ids.mapped('supplier_ids')
    #         record.product_ids = record.market_id.market_line_ids.mapped('product_id')
    @api.depends('market_id')
    def _compute_product(self):
        for rec in self:
            if rec.market_id and rec.market_id.product_ids:
                rec.product_id = rec.market_id.product_ids[0]
            else:
                rec.product_id = False

    def action_to_analyse(self):
        if self.dw_supplier_nature == 'regroupeur':
            return {
                'type': 'ir.actions.act_window',
                'name': 'Manufacturing Document',
                'res_model': 'dw.document.wizard',
                'views': [[self.env.ref('dw_supplier_approval.view_manufacturing_document_wizard').id, 'form']],
                'target': 'new',

                'context': {
                    'default_homologation_id': self.id
                }
            }
        else:
            self.write({"state": "analyse"})

    def action_reject(self):
        self.write({"state": "rejected"})

    def show_purchase_order(self):
        self.ensure_one()

        return {
            'name': 'Purchase Order',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'domain': [('homologation_id', '=', self.id)],
            'context': {
                'default_homologation_id': self.id
            }
            ,
            'views': [(False, 'tree'), (False, 'form')],
            'target': 'current',
        }

    def create_purchase_order(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'BC Echantillion',
            'res_model': 'purchase.order',
            'views': [[self.env.ref('purchase.purchase_order_form').id, 'form']],

            'context': {'create': 0,
                        'default_homologation_id': self.id,
                        'default_partner_id': self.supplier_id.id,
                        'default_order_line': [(0, 0, {'product_id': self.product_id.id,
                                                       'name': self.product_id.name,
                                                       'price_unit': 0.0,
                                                       'product_uom': self.product_id.product_tmpl_id.uom_po_id.id,

                                                       })]
                        }
        }

    def button_prospection(self):
        self.write({"state": "prospection"})

    def _prepare_criteria_line_consultation(self, market_id):
        if not market_id:
            return []
        vals_dict = [
            (0, 0, {'criteria_id': criteria.id}) for criteria in market_id.market_criteria_ids]
        return vals_dict

    def _prepare_consultation(self):
        return {
            'supplier_id': self.supplier_id.id if self.supplier_id else False,
            'dw_supplier_nature': self.dw_supplier_nature if self.supplier_id else False,
            'product_id': self.product_id.id if self.product_id else False,
            'market_id': self.market_id.id if self.market_id else False,
            'homologation_id': self.id,
            'qty': self.qty,
            'company_id': self.company_id.id if self.company_id else False,
            "criteria_line_ids": self._prepare_criteria_line_consultation(self.market_id)
        }

    def action_lunch_consultation(self):
        self.consultation_id = self.env['dw.consultation'].create(self._prepare_consultation())
        if self.consultation_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Consultation',
                'res_model': 'dw.consultation',
                'views': [[self.env.ref('dw_supplier_approval.dw_consultation_form_view').id, 'form']],
                'res_id': self.consultation_id.id,
                'context': {"create": 0},
            }

    def action_create_consultation(self):
        DwConsultatio = self.env['dw.consultation']

        for record in self:
            if record.state != "homologue":
                raise ValidationError(
                    _('This supplier %(supplier_name)s is not homologated for this product %(product_name)s .!',
                      supplier_name=record.supplier_id.name, product_name=record.product_id.name)
                )
            record.consultation_id = DwConsultatio.create(record._prepare_consultation())

    @api.model_create_multi
    def create(self, vals_list):
        IrSequence = self.env['ir.sequence']
        for vals in vals_list:
            if not vals.get("name") or vals['name'] == _('New'):
                vals['name'] = IrSequence.next_by_code('dw.homologation') or _('New')
        return super().create(vals_list)

    def action_load_Pre_eval_quest_file(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'expert Document',
            'res_model': 'dw.document.wizard',
            'views': [[self.env.ref('dw_supplier_approval.view_report_exper_techn_reports_wizard').id, 'form']],
            'target': 'new',

            'context': {
                'default_homologation_id': self.id,

            }
        }

    def action_load_stabilite_file(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'expert Document',
            'res_model': 'dw.document.wizard',
            'views': [[self.env.ref('dw_supplier_approval.view_report_exper_techn_reports_wizard').id, 'form']],
            'target': 'new',

            'context': {
                'default_homologation_id': self.id,

            }
        }

    def action_load_audit_report(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'expert Document',
            'res_model': 'dw.document.wizard',
            'views': [[self.env.ref('dw_supplier_approval.view_report_exper_techn_reports_wizard').id, 'form']],
            'target': 'new',

            'context': {
                'default_homologation_id': self.id,

            }
        }

    def load_reports(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'expert Document',
            'res_model': 'dw.document.wizard',
            'views': [[self.env.ref('dw_supplier_approval.view_report_exper_techn_reports_wizard').id, 'form']],
            'target': 'new',

            'context': {
                'default_homologation_id': self.id,

            }
        }

    def action_to_audit(self):
        self.write({"state": "audit"})

    def action_to_lot_validation_or_qualification(self):

        if self.lot_validation:
            self.write({"state": "lot_validation"})
        else:
            self.write({"state": "qualification"})

    def action_to_qualification(self):
        self.write({"state": "qualification"})

    def action_homologate(self):
        self.write({"state": "homologue"})

    def action_cancel(self):
        self.write({"state": "cancel"})

    def show_documents(self):
        self.ensure_one()
        return {
            'res_model': 'documents.document',
            'type': 'ir.actions.act_window',
            'name': _("%(market_name)s homologations's Documents", market_name=self.name),
            'domain': [
                ('res_model', '=', 'dw.homologation'), ('res_id', '=', self.id),
            ],
            'view_mode': 'kanban,tree,form',

            'context': {'default_res_model': 'dw.homologation', 'default_res_id': self.id,
                        'default_partner_id': self.supplier_id.id if self.supplier_id else False,
                        'default_product_id': self.product_id.id if self.product_id else False,
                        'searchpanel_default_folder_id': self.env.ref("dw_supplier_approval.folder_homologation").id,
                        'limit_folders_to_lead': True},
        }

    def action_show_consultations(self):
        return ({
            'res_model': 'dw.consultation',
            'type': 'ir.actions.act_window',
            'name': _("%(homologation_name)s's Consultations", homologation_name=self.name),

            'domain': [
                ('homologation_id', '=', self.id),
            ],
            'view_mode': 'tree,form',

            'context': {'create': False},
        })

    def action_show_market(self):
        return ({
            'res_model': 'dw.market',
            'type': 'ir.actions.act_window',
            'name': _("%(market_name)s's Market", market_name=self.name),

            'domain': [
                ('homologation_ids', 'in', self.id),
            ],
            'view_mode': 'tree,form',

            'context': {"create": 0},
        })
