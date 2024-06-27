# -*- coding:utf-8 -*-

from odoo import fields, models, api, _


class DwConsultationCriteria(models.Model):
    _inherit = 'dw.consultation.criteria'



class DwConsultationCriteriaLine(models.Model):
    _inherit = 'dw.consultation.criteria.line'

