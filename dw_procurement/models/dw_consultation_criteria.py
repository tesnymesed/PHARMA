# -*- coding:utf-8 -*-
import base64, io, xlsxwriter

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

    def generate_xlsx_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()
        merge_header = workbook.add_format(
            {
                "border": 1,
                "align": "center",
                "valign": "vcenter",
                "fg_color": "#ffff00",
            }
        )
        merge_center = workbook.add_format(
            {
                "border": 1,
                "align": "center",
                "valign": "vcenter",
            }
        )
        merge_format = workbook.add_format(
            {
                "border": 1,
                "align": "center",
                "valign": "vcenter",
                "fg_color": "#92d050",
            }
        )
        worksheet.merge_range('E1:K1', 'TABLEAU COMPARATIF DES OFFRES', merge_header)
        worksheet.merge_range('F2:J2', 'MATIERES PREMIERES ', merge_format)
        worksheet.write('A4', 'Désignation')
        worksheet.merge_range('F4:G4', 'cours devise du', merge_center)
        worksheet.merge_range('I4:K4', 'Fournisseurs consultés', merge_center)
        worksheet.write('A5', 'POSTE N°', merge_center)
        worksheet.write('A6', 'QUANTITE ', merge_center)
        worksheet.merge_range('A8:A9', 'N° ', merge_format)
        worksheet.merge_range('B8:B9', 'Soumissionnaire ', merge_format)
        worksheet.merge_range('C8:C9', 'Fabricants ', merge_format)
        worksheet.merge_range('D8:G8', 'Prix unitaire ', merge_format)
        worksheet.write('D9', 'FOB ', merge_format)
        worksheet.write('E9', 'C&F ', merge_format)
        worksheet.write('F9', 'FCA ', merge_format)
        worksheet.write('G9', 'CPT ', merge_format)
        worksheet.merge_range('H8:H9', 'UM ', merge_format)
        worksheet.merge_range('I8:I9', 'Monnaie ', merge_format)
        worksheet.merge_range('J8:J9', 'Contre valeur en DA ', merge_format)
        worksheet.merge_range('K8:K9', 'Délaien jrs ', merge_format)
        worksheet.merge_range('L8:L9', 'Note: financière (N) ', merge_format)
        worksheet.merge_range('M8:M9', 'Note: délai (N) ', merge_format)
        worksheet.merge_range('N8:N9', 'Note: finale (N) ', merge_format)
        worksheet.merge_range('O8:O9', 'Classement ', merge_format)
        worksheet.merge_range('P8:P9', 'Observation ', merge_format)

        workbook.close()
        attachment_id = self.env['ir.attachment'].create({
            'name': f"{self.display_name} - {_('TCO')}",
            'datas': base64.encodebytes(output.getvalue())
        })
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment_id.id}",
            "target": "download",
        }
