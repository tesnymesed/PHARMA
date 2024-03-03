# -*- coding: utf-8 -*-
{
    'name': 'Sale MRP  Plan',
    'version': '1.0.0',
    'category': 'Localization',
    'description': """
=        """,
    'author': 'DIGIWAVES - ALGERIA',
    'website': 'www.digiwaves.io',
    'depends': [
        'dw_sale_plan', 'dw_mrp_plan'
    ],
    'data': [
        # data
        # report
        'report/mrp_plan_report.xml',

        # security
        'security/ir.model.access.csv',
        'security/security.xml',

        # views
        'views/product_plan_views.xml',

        # wizard

        'menus.xml',
    ],

    'auto_install': True,

    'license': 'LGPL-3',
}
