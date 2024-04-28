from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class DwConsultationCriteria(models.Model):
    _name = 'dw.consultation'
    _description = "Consultation"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(strong="Consultation")
    supplier_id = fields.Many2one("res.partner", String="Supplier", domain='[("is_supplier","=", True)]',
                                  check_company=True, required=1)
    market_id = fields.Many2one('dw.market', string='Market', domain="[('state','=','homologation_cosultation')]")
    supplier_market_id = fields.Many2many(related="market_id.supplier_homologuer_ids")
    homologation_ids = fields.One2many(related="market_id.homologation_ids")
    product_ids = fields.Many2many(related="market_id.product_ids")
    homologation_id = fields.Many2one('dw.homologation', string='Homologation', domain="[('state','in',['homologue'])]")
    product_id = fields.Many2one(
        'product.product', required=1,
        check_company=True,
        domain=['|', '|', ('homologue', '=', True), ('categ_id.homologue', '=', True),
                ('product_tmpl_id.homologue', '=', True), ('purchase_ok', '=', True)],

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

    def action_show_homologation(self):
        return ({
            'res_model': 'dw.homologation',
            'type': 'ir.actions.act_window',
            'name': _("%(consultation_name)s's Consultations", consultation_name=self.name),

            'domain': [
                ('consultation_id', 'in', self.id),
            ],
            'view_mode': 'tree,form',

            'context': {'create': False},
        })
