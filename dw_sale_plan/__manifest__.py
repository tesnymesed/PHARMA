# -*- coding: utf-8 -*-
{
    'name': 'Sale  Plan',
    'version': '1.0.0',
    'category': 'Localization',
    'description': """
=        """,
    'author': 'DIGIWAVES - ALGERIA',
    'website': 'www.digiwaves.io',
    'depends': [
        'sale'
    ],
    'data': [
        # data
        'data/sequence.xml',
        # report
        'report/sale_plan_report.xml',
        # security
        'security/ir.model.access.csv',
        'security/security.xml',

        # views
        'views/res_config_settings_views.xml',
        'views/sales_plan_view.xml',
        # 'views/assets.xml',

        # wizard


        'menus.xml',
    ],
    'qweb': [
        'static/src/xml/monthly_mrp_plan_widget_button.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
