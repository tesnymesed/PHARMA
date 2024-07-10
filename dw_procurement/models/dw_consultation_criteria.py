# -*- coding:utf-8 -*-

from odoo import fields, models, api, _


class DwConsultationCriteria(models.Model):
    _name = 'dw.consultation.criteria'
    _description = "Consultation Criteria"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(strong="Criteria")
    description = fields.Char(strong="Description")
    active = fields.Boolean("Active", default="True")
    criteria_type = fields.Selection(selection=[

        ('amount', 'Based on Amount'),
        ('percentage', 'Based on Percentage'),
        ('period', 'Based on Period'),
        ('boolean', 'Based on boolean'),
    ],
        string="Criteria Type",
        default="amount", )

    period_type = fields.Selection(selection=[

        ('days', 'Based on Days'),
        ('months', 'Based on Months'),
        ('years', 'Based on Years')
    ],
        string="Period Type",
        )


class DwConsultationCriteriaLine(models.Model):
    _name = 'dw.consultation.criteria.line'
    _description = "Consultation Criteria Line"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    consultation_id = fields.Many2one('dw.consultation', string='Consultation', domain="[('active','=',True)]")
    criteria_id = fields.Many2one('dw.consultation.criteria', string='Criteria', domain="[('active','=',True)]")
    name = fields.Char(store=1, related="criteria_id.name")
    supplier_id = fields.Many2one(store=1, related="consultation_id.supplier_id")
    dw_supplier_nature = fields.Selection(store=1, related="consultation_id.dw_supplier_nature")
    product_id = fields.Many2one(store=1, related="consultation_id.product_id")
    criteria_type = fields.Selection(store=1, related="criteria_id.criteria_type")
    amount = fields.Float("Amount")
    percentage = fields.Float("Percentage")
    completed = fields.Boolean(string="completed")
    number_days = fields.Float("Number Days")
    number_years = fields.Float("Number Years")
    number_months = fields.Float("Number Months")
    period_type = fields.Selection(store=1, related="criteria_id.period_type")

    @api.onchange('period_type', 'number_years')
    def onchange_number_years(self):
        if self.criteria_type == 'period' and self.period_type == 'years':
            self.number_days = self.number_years * 365

    @api.onchange('period_type', 'number_months')
    def onchange_number_months(self):
        if self.criteria_type == 'period' and self.period_type == 'months':
            self.number_days = self.number_months * 30

    @api.onchange('period_type')
    def onchange_period_type(self):
        if self.criteria_type != 'period':
            self.number_months = 0
            self.number_years = 0
            self.number_days = 0
        else:
            if self.period_type != 'months':
                self.number_months = 0
            elif self.period_type != 'years':
                self.number_years = 0
