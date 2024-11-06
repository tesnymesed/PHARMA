# -*- coding: utf-8 -*-
{
    'name': 'DW MRP Production Targets [Objectives]',
    'version': '1.0.0',
    'category': 'Manufacturing/Manufacturing',

    'author': 'DIGIWAVES - ALGERIA',
    'website': 'www.digiwaves.io',

    'summary': "Production Targets [Objectives]",
    'description': """ """,
    'depends': ['mrp', 'dw_production_plan_simulator'],
    'data': [
        'security/ir.model.access.csv',
        'views/dw_mrp_production_targets_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
