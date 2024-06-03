# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools.date_utils import start_of, end_of, add, subtract
from odoo.tools.misc import format_date
import datetime


class DWCompany(models.Model):
    _inherit = "res.company"

    manufacturing_period_start = fields.Selection([
        ('present', 'Present'),
        ('year_start', "Current year's start")
    ], string="Manufacturing Period Start",
        default='year_start', required=True,
        help="Default value for the time ranges start (Present Month, or current years's start) in DW Master Production Schedule report.")

    def _get_date_range(self, start_date_range='', end_date_range='', years=False):
        """ Return the date range for a production schedule depending on the
        manufacturing period and the number of columns to display specified by the
        user. It returns a list of tuples that contains the timestamp for each
        column.
        """
        self.ensure_one()
        date_range = []
        if not years:
            years = 0
        manufacturing_period_count = self.manufacturing_period_to_display
        if self.manufacturing_period_start == 'year_start':
            first_day = start_of(subtract(fields.Date.today(), years=years),
                                 'year')
        else:
            first_day = start_of(subtract(fields.Date.today(), years=years),
                                 self.manufacturing_period)
        if start_date_range != '':
            first_day = datetime.datetime.strptime(start_date_range, "%Y-%m-%d").date()
            end_date_range = datetime.datetime.strptime(end_date_range, "%Y-%m-%d").date()
            manufacturing_period_count = self.count_manufacturing_period_to_display(first_day, end_date_range, self.manufacturing_period)
        for columns in range(manufacturing_period_count):
            last_day = end_of(first_day, self.manufacturing_period)
            date_range.append((first_day, last_day))
            first_day = add(last_day, days=1)
        return date_range

    def count_manufacturing_period_to_display(self, start_date_range, end_date_range, manufacturing_period):
        if start_date_range > end_date_range:
            start_date_range, end_date_range = end_date_range, start_date_range
        delta = end_date_range - start_date_range
        days = delta.days
        if manufacturing_period == 'day':
            col_count =  days
        elif manufacturing_period == 'week':
            col_count = days // 7
        else:
            months = (end_date_range.year - start_date_range.year) * 12 + end_date_range.month - start_date_range.month
            if end_date_range.day < start_date_range.day:
                months -= 1
            col_count = months
        return col_count if col_count > 0 else 1

    def _date_range_to_str(self, start_date_range='', end_date_range=''):
        date_range = self._get_date_range(start_date_range=start_date_range, end_date_range=end_date_range)
        dates_as_str = []
        lang = self.env.context.get('lang')
        for date_start, date_stop in date_range:
            if self.manufacturing_period == 'month':
                dates_as_str.append(format_date(self.env, date_start, date_format='MMM yyyy'))
            elif self.manufacturing_period == 'week':
                dates_as_str.append(_('Week %(week_num)s (%(start_date)s-%(end_date)s/%(month)s)',
                    week_num=format_date(self.env, date_start, date_format='w'),
                    start_date=format_date(self.env, date_start, date_format='d'),
                    end_date=format_date(self.env, date_stop, date_format='d'),
                    month=format_date(self.env, date_start, date_format='MMM')
                ))
            else:
                dates_as_str.append(format_date(self.env, date_start, date_format='MMM d'))
        return dates_as_str