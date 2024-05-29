# -*- coding: utf-8 -*-
{
    'name': 'DW MRP Supply Plan',
    'version': '1.0.0',
    'category': 'Localization',
    'description': """
=        """,
    'author': 'DIGIWAVES - ALGERIA',
    'website': 'www.digiwaves.io',
    'depends': [
        'purchase',
        'custom_widget',
    ],
    'data': [
        # data
        'data/supply_plan_data.xml',

        # security
        'security/security.xml',
        'security/ir.model.access.csv',


        # views
        'views/dw_mrp_supply_plan_views.xml',

        'views/menus.xml',

        # wizard
        'wizard/dw_mrp_supply_wizard.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
