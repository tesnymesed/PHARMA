# -*- coding:utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class DwMarket(models.Model):
    _name = 'dw.market'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Supplier Approval"
    name = fields.Char(string="Name")
    state = fields.Selection(
        selection=[
            ('draft', 'Identification of the need'),
            ('prospection', 'Prospection'),
            ('homologation_cosultation', 'Approval/consultation'),
            ('done', 'Assigned'),
            ('cancel', 'Canceled')
        ],
        string="State",
        default="draft",
        store=True,

        group_expand='_expand_states'
    )

    description = fields.Text(string="Description")
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
    )
    user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user)
    product_ids = fields.Many2many(
        'product.product',
        check_company=True,
        domain=['|', '|', ('homologue', '=', True), ('categ_id.homologue', '=', True),
                ('product_tmpl_id.homologue', '=', True), ('purchase_ok', '=', True)],

    )
    supplier_ids = fields.Many2many(
        'res.partner',
        check_company=True,
        domain=[('is_supplier', '=', True)]
    )
    market_type_id = fields.Many2one('dw.market.type', string="Market type")
    consultation_ids = fields.One2many("dw.consultation", 'market_id', string="Consultations")
    homologation_ids = fields.Many2many("dw.homologation", 'market_id', string="Homologation")

    supplier_homologuer_ids = fields.Many2many(
        'res.partner',
        compute="_compute_supplier_homologuer"
    )
    cahier_charge_attachment = fields.Binary(string="Specification document")
    cahier_charge_name = fields.Char(string='File name')
    quantity = fields.Float("Needed Quantity")
    len_supplier_market = fields.Integer("Length Market supplier", store=1, compute="compute_len_supplier_market")
    len_supplier_homologated_market = fields.Integer("Length Market supplier Approved", store=0,
                                                     compute="compute_len_supplier_homologated_market")

    def _expand_states(self, states, domain, order):
        return [key for key, dummy in self._fields['state'].selection]

    def button_draft(self):
        self.write({"state": "draft"})

    @api.depends('supplier_ids')
    def compute_len_supplier_market(self):
        for record in self:
            record.len_supplier_market = len(record.supplier_ids)

    @api.depends('supplier_homologuer_ids')
    def compute_len_supplier_homologated_market(self):
        for record in self:
            record.len_supplier_homologated_market = len(record.supplier_homologuer_ids)

    @api.depends('supplier_ids')
    def _compute_supplier_homologuer(self):
        for record in self:
            search = record.homologation_ids.search([('state', '=', 'homologue'), ('market_id', '=', record.id)])
            supplier_ids = search.mapped('supplier_id')
            record.supplier_homologuer_ids = supplier_ids

    def action_load_spec_file(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Market Document',
            'res_model': 'dw.document.market.wizard',
            'views': [[self.env.ref('dw_supplier_approval.view_document_market_wizard').id, 'form']],
            'target': 'new',

            'context': {
                'default_market_id': self.id
            }
        }

    def action_homologation(self):
        if self.market_type_id and self.market_type_id.forced_nbr_supplier and self.len_supplier_market < self.market_type_id.nbr_supplier:
            raise ValidationError(
                _('The number of supplier must be greater than %(nbr_supplier)s.!',
                  nbr_supplier=self.market_type_id.nbr_supplier)
            )
        self.write({"state": "homologation_cosultation"})

    def action_attribution_file(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Market Document',
            'res_model': 'dw.document.market.wizard',
            'views': [[self.env.ref('dw_supplier_approval.view_document_market_wizard').id, 'form']],
            'target': 'new',

            'context': {
                'default_market_id': self.id
            }
        }

    def action_done(self):
        if self.market_type_id and self.market_type_id.forced_nbr_supplier and self.len_supplier_homologated_market < self.market_type_id.nbr_supplier:
            raise ValidationError(
                _('The number of the Homologated  supplier must be greater than %(nbr_supplier)s.!',
                  nbr_supplier=self.market_type_id.nbr_supplier)
            )

        return {
            'type': 'ir.actions.act_window',
            'name': 'Market Document',
            'res_model': 'dw.attribute.market.wizard',
            'views': [[self.env.ref('dw_supplier_approval.dw_attribute_market_form_view').id, 'form']],
            'target': 'new',

            'context': {
                'default_market_id': self.id
            }
        }

    def show_documents(self):
        self.ensure_one()
        return {
            'res_model': 'documents.document',
            'type': 'ir.actions.act_window',
            'name': _("%(market_name)s 's Documents", market_name=self.name),

            'domain': [
                ('res_model', '=', 'dw.market'), ('res_id', '=', self.id),
            ],
            'view_mode': 'kanban,tree,form',

            'context': {'default_res_model': 'dw.market', 'default_res_id': self.id,

                        'limit_folders_to_lead': True},
        }

    def action_cancel(self):
        self.write({"state": "cancel"})

    def action_prospection(self):

        self.write({"state": "prospection"})

    def action_show_consultations(self):
        return ({
            'res_model': 'dw.consultation',
            'type': 'ir.actions.act_window',
            'name': _("%(market_name)s's Consultations", market_name=self.name),

            'domain': [
                ('market_id', '=', self.id),
            ],
            'view_mode': 'tree,form',

            'context': {'default_market_id': self.id, "create": False if self.state in ["cancel", "done"] else True},
        })

    def action_show_homologations(self):
        return ({
            'res_model': 'dw.homologation',
            'type': 'ir.actions.act_window',
            'name': _("%(market_name)s's homologation", market_name=self.name),

            'domain': [
                ('market_id', '=', self.id),
            ],
            'view_mode': 'tree,form',

            'context': {'default_market_id': self.id, "create": False if self.state in ["cancel", "done"] else True},
        })

    def action_show_consultations_tco(self):
        return ({
            'res_model': 'dw.consultation.criteria.line',
            'type': 'ir.actions.act_window',
            'name': _("%(market_name)s's TCO", market_name=self.name),

            'domain': [
                ('consultation_id.market_id', '=', self.id),
                ('consultation_id.state', '=', 'consulted'),
            ],
            'view_mode': 'tree',

            'context': {'create': False, 'delete': False, 'edit': False, 'duplicate': False,
                        'search_default_criteria_grp': 1, }

        })

    @api.model_create_multi
    def create(self, vals_list):
        IrSequence = self.env['ir.sequence']
        for vals in vals_list:
            if not vals.get("name") or vals['name'] == _('New'):
                seq_name = IrSequence.next_by_code('market.main.seq')

                vals['name'] = seq_name or _('New')
        return super().create(vals_list)
