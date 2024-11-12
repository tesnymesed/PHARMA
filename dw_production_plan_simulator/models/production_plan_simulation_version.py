# -*- coding: utf-8 -*-


from datetime import date

from odoo import fields, models

__SEPARATOR__ = '- V'


class DwDwProductionPlanSimulationVersion(models.Model):
    _name = 'dw.production.plan.simulation.version'
    _description = 'Tracks versions of product simulations and MRP plans by company'

    name = fields.Char('Version Name', required=True,
                       help="Name for the production plan simulation version, e.g., Q1-2024 or Initial Plan.")
    active = fields.Boolean('Active', default=True, help="Indicates if this version is currently active.")
    notes = fields.Text('Notes', help="Additional notes or details about this version.")

    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    simulation_ids = fields.One2many('dw.production.plan.simulation', 'simulation_version_id',
                                     string='Production Simulations')

    def format_name(self, company_id):
        """
        Format the name of the production plan based on the given parameters.

        :param company_id: Company ID for which the plan is being created.
        :return:
        """
        company = self.env['res.company'].browse(company_id)
        company_name = company.name if company else self.env.company.name

        _dseq = date.today().strftime('%Y-%m-%d')
        # Create records in Model 1

        base_name = f'PPROD-SIM/{company_name}-{_dseq}-{__SEPARATOR__}'

        # Check existing names to determine the next version number
        existing_plans = self.env['dw.production.plan.simulation.version'].search([
            ('name', 'ilike', f'{base_name}%'),
            ('company_id', '=', company_id),  # Ensure we are checking within the same company
        ])

        # Determine the next version number
        if existing_plans:
            versions = [int(plan.name.split(__SEPARATOR__)[-1]) for plan in existing_plans if
                        plan.name.split(__SEPARATOR__)[-1].isdigit()]
            try:
                next_version = max(versions) + 1
            except ValueError:
                next_version = 1
        else:
            next_version = 1

        # Create the full name with versioning
        full_name = f'{base_name}{next_version:02d}'  # Formats the version number as two digits (e.g., V01, V02)

        return full_name
