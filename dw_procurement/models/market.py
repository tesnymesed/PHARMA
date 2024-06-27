# -*- coding:utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class DwMarketLine(models.Model):
    _name = 'dw.market.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    product_id = fields.Many2one(
        'product.product',
        check_company=True,
        domain=[('purchase_ok', '=', True)],

    )
    supplier_ids = fields.Many2many(
        'res.partner',
        check_company=True,
        domain=[('is_supplier', '=', True)]
    )
    quantity = fields.Float('Needed Quantity', default=1)
    market_id = fields.Many2one('dw.market')
    company_id = fields.Many2one(
        'res.company', store=1, related="market_id.company_id",
    )
    line_homlogated = fields.Boolean(default=False)
    line_consulted = fields.Boolean(default=False)

class DwMarket(models.Model):
    _name = 'dw.market'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Supplier Approval"
    _order = "start_date desc"
    name = fields.Char(string="Name")
    state = fields.Selection(
        selection=[
            ('draft', 'Identification of the need'),
            ('prospection', 'Prospection'),
            ('consultation', 'consultation'),
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
        compute="_compute_products_ids",
        store="1"
    )
    supplier_ids = fields.Many2many(
        'res.partner',
        check_company=True,
        domain=[('is_supplier', '=', True)]
    )
    market_type_id = fields.Many2one('dw.market.type', string="Market type")
    market_criteria_ids = fields.Many2many('dw.consultation.criteria', string="Market Criteria")
    consultation_ids = fields.One2many("dw.consultation", 'market_id', string="Consultations")

    requisition_ids = fields.One2many("purchase.requisition", 'market_id', string="Attribution")

    market_line_ids = fields.One2many('dw.market.line', 'market_id', string="Market line")
    cahier_charge_attachment = fields.Binary(string="Specification document")
    cahier_charge_name = fields.Char(string='File name')
    len_supplier_market = fields.Integer("Length Market supplier", store=1, compute="compute_len_supplier_market")

    start_date = fields.Date(string="Start Date", default=fields.Date.today)
    end_date = fields.Date(string="End Date", default=fields.Date.today)

    @api.constrains('end_date','start_date')
    def _check_date_start_end(self):
      for record in self:
        if record.start_date and record.end_date:

                if record.start_date > record.end_date:
                    raise ValidationError(
                        _('start date can\'t be greater that end date'))
    @api.depends('market_line_ids')
    def _compute_products_ids(self):
        for record in self:
            record.product_ids = record.market_line_ids.mapped('product_id')

    def _expand_states(self, states, domain, order):
        return [key for key, dummy in self._fields['state'].selection]

    def button_draft(self):
        self.write({"state": "draft"})

    @api.depends('market_line_ids')
    def compute_len_supplier_market(self):
        for record in self:
            record.len_supplier_market = len(record.market_line_ids.mapped('supplier_ids'))

    def action_attribution_file(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Market Document',
            'res_model': 'dw.document.market.wizard',
            'views': [[self.env.ref('dw_procurement.view_document_market_wizard').id, 'form']],
            'target': 'new',

            'context': {
                'default_market_id': self.id
            }
        }
    def action_load_spec_file(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Market Document',
            'res_model': 'dw.document.market.wizard',
            'views': [[self.env.ref('dw_procurement.view_document_market_wizard').id, 'form']],
            'target': 'new',

            'context': {
                'default_market_id': self.id
            }
        }

    def action_load_cahier_charge(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Market Document',
            'res_model': 'dw.document.market.wizard',
            'views': [[self.env.ref('dw_procurement.view_document_market_wizard').id, 'form']],
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
                        'searchpanel_default_folder_id': self.env.ref("dw_procurement.folder_dw_market").id,
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

            'context': {'default_market_id': self.id, "create": 0},
        })



    def action_show_Attribution(self):
        return ({
            'res_model': 'purchase.requisition',
            'type': 'ir.actions.act_window',
            'name': _("%(market_name)s's Attribution", market_name=self.name),

            'domain': [
                ('market_id', '=', self.id),
            ],
            'view_mode': 'tree,form',

            'context': {'default_market_id': self.id, "create": 0},
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
