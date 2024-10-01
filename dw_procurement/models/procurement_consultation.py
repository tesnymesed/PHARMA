from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class DwConsultationCriteria(models.Model):
    _name = 'procurement.dw.consultation'
    _description = "Consultation"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "start_date desc"

    name = fields.Char(strong="Consultation")
    supplier_id = fields.Many2one("res.partner", String="Supplier", domain='[("is_supplier","=", True)]',
                                  check_company=True, required=1)

    market_id = fields.Many2one('procurement.market.dw', string='Market', check_company=True, )
    for_approval = fields.Boolean("for Approval ?", compute="_compute_for_approval")

    product_id = fields.Many2one(
        'product.product', required=1,
        check_company=True,
        domain=[('purchase_ok', '=', True)],

    )

    display_name = fields.Char("Dsiplay name", compute="_compute_display_name", store="1")
    company_id = fields.Many2one(
        'res.company', required=1,
        default=lambda self: self.env.company,
    )
    criteria_line_ids = fields.One2many(
        'procurement.dw.consultation.criteria.line',
        'consultation_id',
    )
    qty = fields.Float("Quantity")
    user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user)
    active = fields.Boolean("Active", default="True")
    state = fields.Selection(selection=[

        ('draft', 'Draft'),
        ('consulted', 'Consulted'),
        ('allocated', 'Allocated'),
        ('reject', 'Reject'),
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
    canceled_motif_id = fields.Many2one('procurement.reject.cancel.reason', string='Reason',
                                        domain=[('reason_type', '=', 'cancel')],
                                        )
    reject_motif_id = fields.Many2one('procurement.reject.cancel.reason', string='Reject Reason',
                                      domain=[('reason_type', '=', 'reject')],
                                      )

    @api.constrains('end_date', 'start_date')
    def _check_date_start_end(self):
        for record in self:
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

    @api.depends('market_id', 'product_id')
    def _compute_for_approval(self):
        for record in self:
            market_id = record.market_id
            product_id = record.product_id
            record.for_approval = market_id.for_approval if market_id else product_id.need_approval if product_id else False

    @api.model_create_multi
    def create(self, vals_list):
        IrSequence = self.env['ir.sequence']
        for vals in vals_list:
            if not vals.get("name") or vals['name'] == _('New'):
                vals['name'] = IrSequence.next_by_code('consultation.main.seq') or _('New')
        return super().create(vals_list)

    def action_draft(self):
        self.write({"state": 'draft', "canceled_motif_id": False, "reject_motif_id": False})

    def action_consulted(self):
        for line in self.criteria_line_ids:
            criteria_type = line.criteria_type
            criteria_id_name = line.criteria_id.name
            if criteria_type == "period":
                if line.period_type == "days" and not line.number_days:
                    raise ValidationError(
                        _('You cannot mark as consulted for this Criteria %(criteria_name)s , you should introduce number of days .!',
                          criteria_name=criteria_id_name)
                    )
            elif criteria_type == "amount" and not line.amount:
                raise ValidationError(
                    _('You cannot mark as consulted for this Criteria %(criteria_name)s , you should introduce Amount .!',
                      criteria_name=criteria_id_name)
                )
            elif criteria_type == "percentage" and not line.percentage:
                raise ValidationError(
                    _('You cannot mark as consulted for this Criteria %(criteria_name)s , you should introduce percentage .!',
                      criteria_name=criteria_id_name)
                )
        self.write({"state": 'consulted'})

    def button_canceled(self):
        self.write({"state": 'canceled'})
        return {'type': 'ir.actions.act_window_close'}

    def action_canceled(self):
        self.ensure_one()
        return ({
            'res_model': 'procurement.dw.consultation',
            'type': 'ir.actions.act_window',
            'name': _("Cancel Motif for consultation : %(consultation_name)s", consultation_name=self.name),
            'res_id': self.id,
            "target": "new",
            'views': [[self.env.ref('dw_procurement.dw_consultation_form_view_canceled').id, 'form']],
            'context': {'create': False, 'dw_consultation_cancel_reason': True},
        })

    def button_reject(self):
        self.write({"state": 'reject'})
        return {'type': 'ir.actions.act_window_close'}

    def action_reject(self):
        self.ensure_one()
        return ({
            'res_model': 'procurement.dw.consultation',
            'type': 'ir.actions.act_window',
            'name': _("Reject Motif for consultation : %(consultation_name)s", consultation_name=self.name),
            'res_id': self.id,
            "target": "new",
            'views': [[self.env.ref('dw_procurement.dw_consultation_form_view_canceled').id, 'form']],
            'context': {'create': False, 'dw_consultation_reject_reason': True},
        })

    def action_show_market(self):
        return ({
            'res_model': 'procurement.market.dw',
            'type': 'ir.actions.act_window',
            'name': _("%(consultation_name)s's Consultations", consultation_name=self.name),

            'domain': [
                ('consultation_ids', 'in', self.id),
            ],
            'view_mode': 'tree,form',

            'context': {'create': False},
        })

    def action_show_Attribution(self):
        if self.market_id:
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

    @api.constrains('state', 'active', 'market_id', 'product_id')
    def _check_unique_market_consultation_product(self):
        for record in self:
            if not record.market_id or not record.product_id or not record.supplier_id:
                continue
            market_id = record.market_id
            product_id = record.product_id
            supplier_id = record.supplier_id
            domain = [
                ('id', '!=', record.id),
                ('active', '=', True),
                ('state', 'not in', ['reject', 'canceled']),
                ('market_id', '=', market_id.id),
                ('product_id', '=', product_id.id),
                ('supplier_id', '=', supplier_id.id)
            ]

            if self.search_count(domain):
                raise ValidationError(
                    _('A consultation already exists for this supplier : %(supplier_name)s, market : %(market_name)s, and product : %(product_name)s.',
                      supplier_name=supplier_id.name, market_name=market_id.name,
                      product_name=product_id.name)

                )
