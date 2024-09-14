# -*- coding:utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class DwMarketLine(models.Model):
    _name = 'procurement.market.dw.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    supplier_ids = fields.Many2many(
        'res.partner',
        check_company=True,
        domain=[('is_supplier', '=', True)]
    )
    product_id = fields.Many2one(
        'product.product',
        check_company=True,
        domain=[('purchase_ok', '=', True)],
    )
    quantity = fields.Float('Needed Quantity', default=1)
    market_id = fields.Many2one('procurement.market.dw')
    company_id = fields.Many2one(
        'res.company', store=1, related="market_id.company_id",
    )
    line_approved = fields.Boolean(default=False)
    line_consulted = fields.Boolean(default=False)

    def action_to_consult(self):
        line_id = self
        supplier_ids = line_id.mapped("supplier_ids")
        product_id = line_id.product_id
        market_id = line_id.market_id
        consultation_ids = market_id.mapped("consultation_ids").filtered(
            lambda c: c.product_id == product_id and c.state not in ['canceled'])

        suppliers_without_consultation = supplier_ids.filtered(
            lambda supplier: not consultation_ids.filtered(lambda cons: cons.supplier_id == supplier)
        )
        if not suppliers_without_consultation:
            raise ValidationError(
                _('There is no more supplier to consult for this market %(market_name)s.',
                  market_name=market_id.name)
            )
        quantity = line_id.quantity
        line_ids = self.env["procurement.wizard.line"].create([
            {'supplier_id': supplier.id, 'line_id': self.id, 'product_id': product_id.id, 'quantity': quantity} for
            supplier in suppliers_without_consultation])

        return {
            'type': 'ir.actions.act_window',
            'name': 'Market Document',
            'res_model': 'procurement.wizard.line',
            'views': [[self.env.ref('dw_procurement.dw_procurement_market_consultation_wizard_tree_view').id, 'tree']],
            'target': 'new',
            'domain': [
                ('id', '=', line_ids.ids or False),
            ],
            'context': {
                'default_line_id': self.id,
                'default_market_id': self.market_id.id
            }
        }


class DwMarket(models.Model):
    _name = 'procurement.market.dw'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Supplier Approval"
    _order = "start_date desc"
    name = fields.Char(string="Name")
    state = fields.Selection(
        selection=[
            ('draft', 'Identification of the need'),
            ('prospecting', 'prospecting'),
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
        'res.partner', compute="compute_supplier_market", store="1",
        check_company=True,
        domain=[('is_supplier', '=', True), ]
    )
    market_type_id = fields.Many2one('procurement.market.dw.type', string="Procurement method")
    market_criteria_ids = fields.Many2many('procurement.dw.consultation.criteria', string="Market Criteria")
    consultation_ids = fields.One2many("procurement.dw.consultation", 'market_id', string="Consultations")

    requisition_ids = fields.One2many("purchase.requisition", 'market_id', string="Attribution")

    market_line_ids = fields.One2many('procurement.market.dw.line', 'market_id', string="Market line")
    cahier_charge_attachment = fields.Binary(string="Specification document")
    cahier_charge_name = fields.Char(string='File name')
    len_supplier_market = fields.Integer("Length Market supplier", store=1, compute="compute_len_supplier_market")
    motif_id = fields.Many2one('procurement.reject.cancel.reason', 'Reason')
    start_date = fields.Date(string="Start Date", default=fields.Date.today)
    end_date = fields.Date(string="End Date", default=fields.Date.today)
    for_approval = fields.Boolean("for approval")

    def action_done(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'Market Document',
            'res_model': 'dw.attribute.market.wizard',
            'views': [[self.env.ref('dw_procurement.dw_attribute_market_form_view').id, 'form']],
            'target': 'new',

            'context': {
                'default_market_id': self.id
            }
        }

    def action_confirm(self):
        if self.market_type_id and self.market_type_id.forced_nbr_supplier and self.len_supplier_market < self.market_type_id.nbr_supplier:
            raise ValidationError(
                _('The number of supplier must be greater than %(nbr_supplier)s.!',
                  nbr_supplier=self.market_type_id.nbr_supplier)
            )
        self.write({"state": "consultation"})

    @api.constrains('end_date', 'start_date')
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

    @api.depends('market_line_ids')
    def compute_supplier_market(self):
        for record in self:
            record.supplier_ids = record.market_line_ids.mapped('supplier_ids')

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
                ('res_model', '=', 'procurement.market.dw'), ('res_id', '=', self.id),
            ],
            'view_mode': 'kanban,tree,form',

            'context': {'default_res_model': 'procurement.market.dw', 'default_res_id': self.id,
                        'searchpanel_default_folder_id': self.env.ref("dw_procurement.folder_dw_market").id,
                        'limit_folders_to_lead': True},
        }

    def action_cancel(self):
        self.write({"state": "cancel"})

    def action_prospecting(self):

        self.write({"state": "prospecting"})

    def action_show_consultations(self):

        return ({
            'res_model': 'procurement.dw.consultation',
            'type': 'ir.actions.act_window',
            'name': _("%(market_name)s's Consultations", market_name=self.name),

            'domain': [('market_id', '=', self.id)
                       ],
            'view_mode': 'tree,form',

            'context': {'default_market_id': self.id, "create": 1,
                        'default_criteria_line_ids': [
                            (0, 0, {'criteria_id': criteria.id}) for criteria in self.market_criteria_ids]
                        },
        })

    def action_show_consultation(self):

        return ({
            'res_model': 'procurement.dw.consultation',
            'type': 'ir.actions.act_window',
            'name': _("%(market_name)s's Consultations", market_name=self.name),

            'domain': [('market_id', '=', self.id)
                       ],
            'view_mode': 'tree,form',

            'context': {'default_market_id': self.id, "create": 0,
                        },
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
            'res_model': 'procurement.dw.consultation.criteria.line',
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
