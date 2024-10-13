# -*- coding:utf-8 -*-
import json

from odoo import api, fields, models
from odoo.osv import expression


class DwPharmaAccessMixin(models.AbstractModel):
    _name = 'dw.pharma.resource.access.mixin'
    _description = "DW Pharma Resource Access Mixin"

    dw_simulation_ok = fields.Boolean('Simulation OK', index=True, store=True)

    @api.model
    def _apply_search_filter(self):
        return True

    def fetch(self, field_names):
        return super(DwPharmaAccessMixin,
                     self.with_context(dw_bypass_pharma_simulation=True)).fetch(field_names)

    def _fetch_query(self, query, fields):
        context = self._context or {}
        if context.get('dw_pharma_simulation', False):
            self = self.with_context(dw_bypass_pharma_simulation=True)

        return super(DwPharmaAccessMixin, self)._fetch_query(query, fields)

    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        """ Override _search in order to search on VN Product """
        context = self._context or {}

        # If dw_pharma_simulation is in context then filter on vn products only
        if self._apply_search_filter():
            if not context.get('dw_bypass_pharma_simulation'):
                if context.get('dw_pharma_simulation', False):
                    domain = expression.AND([domain, [('dw_simulation_ok', '=', True)]])
                else:
                    domain = expression.AND([domain, [('dw_simulation_ok', '!=', True)]])

        # Call super
        return super(DwPharmaAccessMixin, self)._search(domain, offset=offset, limit=limit, order=order,
                                                        access_rights_uid=access_rights_uid)

    @api.model
    def default_get(self, fields_list):
        # Call super method to get the default values dict
        defaults = super(DwPharmaAccessMixin, self).default_get(fields_list)

        # Get context
        context = self._context or {}

        if context.get('dw_pharma_simulation', False):
            defaults['dw_simulation_ok'] = True

        # Return defaults
        return defaults

    @api.model
    def _get_context_fields(self):
        return []

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        fields_list = self._get_context_fields()
        # we have to do this again because of the context is applied in all actions
        context = self._get_global_context(options.get('action_id'))
        if context.get('dw_pharma_simulation'):
            if view_type in ('form', 'tree'):
                for fname in fields_list:
                    for node in arch.xpath("//field[@name='%s']" % fname):
                        if "context" in node.attrib:
                            context_str = self._sanitize_context_attribute(node.attrib["context"])
                            context = json.loads(context_str)
                            context['dw_pharma_simulation'] = True
                            node.attrib["context"] = json.dumps(context)
                        else:
                            node.attrib["context"] = "{'dw_pharma_simulation': True}"
        return arch, view

    def _sanitize_context_attribute(self, context_str):
        return context_str.replace("'", "\"").replace("True", "true").replace("False", "false").replace("None",
                                                                                                        "false").replace(
            '\n', '').replace(' ', '').replace(',}', '}')

    def _get_global_context(self, action_id=None):
        context = self.env.context
        if not action_id or action_id in [453, 410, 267, 411]:
            return context

        b_action = self.env['ir.actions.actions'].sudo().browse(action_id)
        action_type = b_action.type
        action = self.env[action_type].sudo().browse(action_id)

        action_context_str = self._sanitize_context_attribute(action.context or "{}")
        if 'allowed_company_ids[0]' in action_context_str:
            if hasattr(self, 'allowed_company_ids') and self.allowed_company_ids:
                # Replace the placeholder with the actual value from the list
                action_context_str = action_context_str.replace("allowed_company_ids[0]",
                                                                str(self.allowed_company_ids[0]))
            else:
                action_context_str = action_context_str.replace(",\"default_company_id\":allowed_company_ids[0]", '')
        action_context = json.loads(action_context_str)
        # try:
        #     action_context = json.loads(action_context_str)
        # except json.JSONDecodeError as e:
        #     print(f"Error parsing JSON: {e}")
        #     return context
        return dict(
            **context,
            **action_context
        )
