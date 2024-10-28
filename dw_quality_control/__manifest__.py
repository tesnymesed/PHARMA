# -*- coding: utf-8 -*-
{
    'name': 'Quality Control - PHARMA',
    'version': '1.0.0',
    'category': 'Localization',
    'description': """
=        """,
    'author': 'DIGIWAVES - ALGERIA',
    'website': 'www.digiwaves.io',
    'depends': [
        'quality_control','mrp_workorder'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/sample_sequence.xml',
        'views/quality_check_model_views.xml',
        'views/product_views.xml',
        'views/quality_check_views.xml',
        'views/stock_location.xml',
        'views/stock_warehouse.xml',
        'views/sample_request_view.xml',
        'views/res_config_settings_inherit_views.xml',

        'wizard/dw_quality_lot_approval_views.xml',
        'wizard/dw_quality_reload_views.xml',

    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
