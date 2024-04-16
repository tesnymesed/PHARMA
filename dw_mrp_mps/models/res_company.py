# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools.date_utils import start_of, end_of, add, subtract
from odoo.tools.misc import format_date


class DWCompany(models.Model):
    _inherit = "res.company"

    manufacturing_period_start = fields.Selection([
        ('present', 'Present'),
        ('year_start', "Current year's start")
    ], string="Manufacturing Period Start",
        default='year_start', required=True,
        help="Default value for the time ranges start (Present Month, or current years's start) in DW Master Production Schedule report.")

    def _get_date_range(self, years=False):
        """ Return the date range for a production schedule depending on the
        manufacturing period and the number of columns to display specified by the
        user. It returns a list of tuples that contains the timestamp for each
        column.
        """
        self.ensure_one()
        date_range = []
        if not years:
            years = 0

        if self.manufacturing_period_start == 'year_start':
            first_day = start_of(subtract(fields.Date.today(), years=years),
                                 'year')
        else:
            first_day = start_of(subtract(fields.Date.today(), years=years),
                                 self.manufacturing_period)

        for columns in range(self.manufacturing_period_to_display):
            last_day = end_of(first_day, self.manufacturing_period)
            date_range.append((first_day, last_day))
            first_day = add(last_day, days=1)
        return date_range
