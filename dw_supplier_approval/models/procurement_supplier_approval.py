# -*- coding:utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class ProcurementSupplierApproval(models.Model):
    _name = 'procurement.supplier.approval'
    _description = "supplier approval"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "start_date desc"

    name = fields.Char(string='Name', default=lambda self: _('New'), copy=False)

    state = fields.Selection(
        selection=[
            ('prospecting', 'prospecting'),
            ('analyse', 'Analyse'),
            ('audit', 'Audit'),
            ('rejected', 'Rejected'),
            ('lot_validation', 'Lot Validation'),
            ('qualification', 'Qualification'),
            ('approval', 'approved'),
            ('cancel', 'Canceled')
        ],
        string="State",
        default="prospecting",
        group_expand='_expand_states'
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
    )
    product_id = fields.Many2one(
        'product.product',
        check_company=True,
        readonly=False, store=True, required="1",
        domain=['|', '|', ('need_approval', '=', True), ('categ_id.need_approval', '=', True),
                ('product_tmpl_id.need_approval', '=', True), ('purchase_ok', '=', True)],
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
    market_supplier_ids = fields.Many2many('res.partner', store="1")

    email = fields.Char('Email', related="supplier_id.email", readonly=False, store=1)

    phone = fields.Char('Phone', related="supplier_id.phone", readonly=False, store=1)
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
    stability_file_attachment = fields.Binary(string="Fichier de stabilité")
    stability_file_file_name = fields.Char(string='File name')
    qty = fields.Float("Quantity")
    dw_manufacturer = fields.Char(string="Manufacturer")
    dw_product_pharma_family_name = fields.Char("Family Name", related="product_id.dw_pharma_family_id.name", store=1)
    motif_id = fields.Many2one('procurement.reject.cancel.reason', 'Reason')

    @api.constrains('end_date', 'start_date')
    def _check_date_start_end(self):
        for record in self:
            if record.start_date and record.end_date:

                if record.start_date > record.end_date:
                    raise ValidationError(
                        _('start date can\'t be greater that end date'))

    def _expand_states(self, states, domain, order):
        return [key for key, dummy in self._fields['state'].selection]



    def action_to_analyse(self):
        if self.dw_supplier_nature == 'regroupeur':
            return {
                'type': 'ir.actions.act_window',
                'name': 'Manufacturing Document',
                'res_model': 'dw.document.wizard',
                'views': [[self.env.ref('dw_supplier_approval.view_manufacturing_document_wizard').id, 'form']],
                'target': 'new',

                'context': {
                    'default_approval_id': self.id
                }
            }
        self.write({"state": "analyse"})

    def action_reject(self):
        self.write({"state": "rejected"})


    def button_prospecting(self):
        self.write({"state": "prospecting"})

    @api.model_create_multi
    def create(self, vals_list):
        IrSequence = self.env['ir.sequence']
        for vals in vals_list:
            if not vals.get("name") or vals['name'] == _('New'):
                vals['name'] = IrSequence.next_by_code('procurement.supplier.approval') or _('New')
        return super().create(vals_list)


    def action_load_Pre_eval_quest_file(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'expert Document',
            'res_model': 'dw.document.wizard',
            'views': [[self.env.ref('dw_supplier_approval.view_report_exper_techn_reports_wizard').id, 'form']],
            'target': 'new',

            'context': {
                'default_approval_id': self.id,

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
                'default_approval_id': self.id,

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
                'default_approval_id': self.id,

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
                'default_approval_id': self.id,

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
        self.write({"state": "approval"})

    def action_cancel(self):
        self.write({"state": "cancel"})

    def show_documents(self):
        self.ensure_one()
        return {
            'res_model': 'documents.document',
            'type': 'ir.actions.act_window',
            'name': _("%(market_name)s approvals's Documents", market_name=self.name),
            'domain': [
                ('res_model', '=', 'procurement.supplier.approval'), ('res_id', '=', self.id),
            ],
            'view_mode': 'kanban,tree,form',

            'context': {'default_res_model': 'procurement.supplier.approval', 'default_res_id': self.id,
                        'default_partner_id': self.supplier_id.id if self.supplier_id else False,
                        'default_product_id': self.product_id.id if self.product_id else False,
                        'searchpanel_default_folder_id': self.env.ref("dw_supplier_approval.folder_supplier_approval").id,
                        'limit_folders_to_lead': True},
        }

    @api.constrains('supplier_id', 'product_id', 'company_id')
    def _single_engoing_approval(self):
        for rec in self:
            existing_record = self.search([
                ('supplier_id', '=', rec.supplier_id.id),
                ('product_id', '=', rec.product_id.id),
                ('company_id', '=', rec.company_id.id),('state', 'in', ['approval']),
                ('id', '!=', rec.id)
            ],)
            if existing_record:
                raise ValidationError("A record with this Supplier, company and Product already exists.")
