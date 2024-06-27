# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime

from odoo import fields, models
from odoo.tools.date_utils import start_of, end_of, add, subtract


class DWCompany(models.Model):
    _inherit = "res.company"

    dw_prod_sim_periods_to_display = fields.Integer('Number of columns for the\
        given period to display in Production Plan Simulation Tool', default=12)

    dw_prod_sim_date_range_start = fields.Date('ProdSim Range Start', readonly=True)
    dw_prod_sim_date_range_end = fields.Date('ProdSim Range End', readonly=True)

    def set_prod_sim_date_range(self, date_start='', date_end=''):
        self.ensure_one()

        if date_start and date_end:
            date_start = fields.Date.from_string(date_start)
            date_end = fields.Date.from_string(date_end)

            _period_count = self.count_manufacturing_period_to_display(date_start, date_end, 'month')
            self.write({
                'dw_prod_sim_date_range_start': date_start,
                'dw_prod_sim_date_range_end': date_end,
                'dw_prod_sim_periods_to_display': _period_count,

            })

    def _get_simulation_date_range(self, years=False):
        """ Return the date range for a production plan simulator depending on the
        manufacturing period and the number of columns to display specified by the
        user. It returns a list of tuples that contains the timestamp for each
        column.
        """
        self.ensure_one()
        date_range = []
        if not years:
            years = 0

        manufacturing_period_count = self.dw_prod_sim_periods_to_display

        if self.manufacturing_period_start == 'year_start':
            first_day = start_of(subtract(fields.Date.today(), years=years),
                                 'year')
        else:
            first_day = start_of(subtract(fields.Date.today(), years=years),
                                 self.manufacturing_period)

        if self.dw_prod_sim_date_range_start:
            first_day = self.dw_prod_sim_date_range_start

        if self.dw_prod_sim_date_range_end:
            last_day = self.dw_prod_sim_date_range_end
        else:
            last_day = end_of(first_day, 'year')

        if not manufacturing_period_count:
            manufacturing_period_count = self.count_manufacturing_period_to_display(first_day, last_day, 'month')


        for columns in range(manufacturing_period_count):
            last_day = end_of(first_day, 'month')
            date_range.append((first_day, last_day))
            first_day = add(last_day, days=1)

        return date_range
