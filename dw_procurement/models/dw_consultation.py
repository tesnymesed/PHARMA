from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class DwConsultationCriteria(models.Model):
    _name = 'dw.consultation'
    _description = "Consultation"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "start_date desc"

    name = fields.Char(strong="Consultation")
    supplier_id = fields.Many2one("res.partner", String="Supplier", domain='[("is_supplier","=", True)]',
                                  check_company=True, required=1)
    supplier_domain_ids = fields.Many2many("res.partner",String="Supplier",domain='[("is_supplier","=", True)]', compute="_compute_supplier_domain_ids")
    market_id = fields.Many2one('dw.market', string='Market')
    dw_for_homologation = fields.Boolean("for homologation", related="market_id.dw_for_homologation")


    product_ids = fields.Many2many(related="market_id.product_ids")

    product_id = fields.Many2one(
        'product.product', required=1,
        check_company=True,
        domain=[('purchase_ok', '=', True)],

    )
    product_domain_ids = fields.Many2many(
        'product.product',
        domain=[('purchase_ok', '=', True)],compute="_compute_product_domain_ids"

    )
    display_name = fields.Char("Dsiplay name", compute="_compute_display_name", store="1")
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
    )
    criteria_line_ids = fields.One2many(
        'dw.consultation.criteria.line',
        'consultation_id',
    )
    qty = fields.Float("Quantity")
    user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user)
    active = fields.Boolean("Active", default="True")
    state = fields.Selection(selection=[

        ('draft', 'Draft'),
        ('consulted', 'Consulted'),
        ('allocated', 'Allocated'),
        ('canceled', 'Canceled')
    ],
        string="State",
        default="draft", )
    start_date = fields.Date(string="Start Date", default=fields.Date.today)
    end_date = fields.Date(string="End Date", default=fields.Date.today)
    dw_supplier_nature = fields.Selection(
        [('fabricant', 'Fabricant'), ('regroupeur', 'Regroupeur')],
        string="Supplier nature", related="supplier_id.dw_supplier_nature", readonly=False, store=True,
    )

    @api.depends('market_id')
    def _compute_supplier_domain_ids(self):
       for rec in self :
           if rec.market_id:
               rec.supplier_domain_ids = rec.market_id.supplier_ids
           else :
               rec.supplier_domain_ids = self.env['res.partner'].search([("is_supplier", "=", True)])

    @api.depends('market_id')
    def _compute_product_domain_ids(self):
        for rec in self:
            if rec.market_id:
                rec.product_domain_ids = rec.market_id.product_ids
            else:
                rec.product_domain_ids = self.env['product.product'].search([('purchase_ok', '=', True)])

    @api.constrains('end_date', 'start_date')
    def _check_date_start_end(self):
       for record in self :
        if record.start_date and record.end_date:

            if record.start_date > record.end_date:
                raise ValidationError(
                    _('start date can\'t be greater that end date'))
    @api.depends('name', 'supplier_id')
    def _compute_display_name(self):
        for record in self:
            final_name = ""

            final_name = final_name + record.name if record.name else ""
            if record.supplier_id:
                final_name = final_name + " " + record.supplier_id.name
                record.display_name = final_name

    @api.model_create_multi
    def create(self, vals_list):
        IrSequence = self.env['ir.sequence']
        for vals in vals_list:
            if not vals.get("name") or vals['name'] == _('New'):
                vals['name'] = IrSequence.next_by_code('consultation.main.seq') or _('New')
        return super().create(vals_list)

    def action_draft(self):
        self.write({"state": 'draft'})

    def action_consulted(self):
        for line in self.criteria_line_ids:
            if line.criteria_type == "period":
                if line.period_type == "days" and not line.number_days:
                    raise ValidationError(
                        _('You cannot mark as consulted for this Criteria %(criteria_name)s , you should introduce number of days .!',
                          criteria_name=line.criteria_id.name)
                    )
            elif line.criteria_type == "amount" and not line.amount:
                raise ValidationError(
                    _('You cannot mark as consulted for this Criteria %(criteria_name)s , you should introduce Amount .!',
                      criteria_name=line.criteria_id.name)
                )
            elif line.criteria_type == "percentage" and not line.percentage:
                raise ValidationError(
                    _('You cannot mark as consulted for this Criteria %(criteria_name)s , you should introduce percentage .!',
                      criteria_name=line.criteria_id.name)
                )
        self.write({"state": 'consulted'})

    def action_canceled(self):
        self.write({"state": 'canceled'})

    def action_show_market(self):
        return ({
            'res_model': 'dw.market',
            'type': 'ir.actions.act_window',
            'name': _("%(consultation_name)s's Consultations", consultation_name=self.name),

            'domain': [
                ('consultation_ids', 'in', self.id),
            ],
            'view_mode': 'tree,form',

            'context': {'create': False},
        })


    def action_show_Attribution(self):
        if self.market_id :
            return ({
                'res_model': 'purchase.requisition',
                'type': 'ir.actions.act_window',
                'name': _("%(market_name)s's Attribution", market_name=self.market_id.name),

                'domain': [
                    ('market_id', '=', self.market_id.id),
                ],
                'view_mode': 'tree,form',

                'context': {'default_market_id': self.market_id.id, "create": 0},
            })
