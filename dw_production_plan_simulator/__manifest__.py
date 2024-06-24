# -*- coding: utf-8 -*-
{
    'name': "DW Production Plan Simulator",

    'version': '1.0.0',
    'category': 'Manufacturing/Manufacturing',

    'author': 'DIGIWAVES - ALGERIA',
    'website': 'www.digiwaves.io',
    'summary': "Simulate and evaluate production plans",

    'description': """
    This module provides a production plan simulator that allows users to input production details, such as product, quantity, production date, and workshop. The simulator then calculates the available capacity and material requirements, and determines the feasibility of the production plan.
    
    Key Features:
    - Input production plan details
    - Compute capacity required and available
    - Calculate material required and available
    - Determine the feasibility of the production plan
    - Display alert messages for capacity and material constraints
    """,
    'depends': ['web', 'shared_assets'],
    'data': [
        # data

        # security
        # 'security/security.xml',
        'security/ir.model.access.csv',
        #
        # views
        'views/views.xml',
        'views/menus.xml',

    ],

    'assets': {
        'web.assets_backend': [
            'dw_production_plan_simulator/static/src/models/production_plan_simulator_model.js',

            'dw_production_plan_simulator/static/src/components/line.js',
            'dw_production_plan_simulator/static/src/components/line.xml',
            'dw_production_plan_simulator/static/src/components/line.scss',

            'dw_production_plan_simulator/static/src/components/main.js',
            'dw_production_plan_simulator/static/src/components/main.xml',
            'dw_production_plan_simulator/static/src/components/main.scss',

        ],
    },

    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
