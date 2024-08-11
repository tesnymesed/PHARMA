from odoo import models, fields


class MRPSupplyWizardGroupingOption(models.Model):
    _name = 'dw.mrp.supply.wizard.grouping.option'
    _description = 'MRP Supply Wizard Grouping Criterias'

    name = fields.Selection([
        ('partner', 'Supplier'),
        ('incoterm', 'Incoterm'),
        ('company', 'Company')
    ], string='Grouping Criteria', required=True)
