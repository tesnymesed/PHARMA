# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict, namedtuple
from dateutil.relativedelta import relativedelta
from math import log10

from odoo import api, fields, models, _


class DWMrpProductionSchedule(models.Model):
    _inherit = 'mrp.production.schedule'

    @api.model
    def get_mps_view_state(self, domain=False, offset=0, limit=False):
        """ Return the global information about MPS and a list of production
        schedules values with the domain.

        :param domain: domain for mrp.production.schedule
        :return: values used by the client action in order to render the MPS.
            - dates: list of period name
            - date_objs: list of period Date objects
            - production_schedule_ids: list of production schedules values
            - manufacturing_period: list of periods (days, months or years)
            - company_id: user current company
            - groups: company settings that hide/display different rows
        :rtype: dict
        """

        config = super(DWMrpProductionSchedule, self).get_mps_view_state(domain=False, offset=0, limit=False)
        config['date_objs'] = self.env.company._get_date_range()
        return config
