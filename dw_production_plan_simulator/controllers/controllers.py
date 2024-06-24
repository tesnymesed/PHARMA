# -*- coding: utf-8 -*-
# from odoo import http


# class DwProductionPlanSimulator(http.Controller):
#     @http.route('/dw_production_plan_simulator/dw_production_plan_simulator', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dw_production_plan_simulator/dw_production_plan_simulator/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('dw_production_plan_simulator.listing', {
#             'root': '/dw_production_plan_simulator/dw_production_plan_simulator',
#             'objects': http.request.env['dw_production_plan_simulator.dw_production_plan_simulator'].search([]),
#         })

#     @http.route('/dw_production_plan_simulator/dw_production_plan_simulator/objects/<model("dw_production_plan_simulator.dw_production_plan_simulator"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dw_production_plan_simulator.object', {
#             'object': obj
#         })
