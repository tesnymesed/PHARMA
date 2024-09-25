# -*- coding: utf-8 -*-
{
    'name': 'MRP  BASE',
    'version': '1.0.0',
    'category': 'Manufacturing',
    'description': """
=        """,
    'author': 'DIGIWAVES - ALGERIA',
    'website': 'www.digiwaves.io',
    'depends': [
        'mrp',
        'product_expiry'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/dw_mrp_bom_form.xml',
        'views/dw_mrp_bom_form.xml',
        'views/mrp_bom_views.xml',
        'views/mrp_workorder_views.xml',
        'views/mrp_production_views.xml',
        'wizard/mrp_production_lot_views.xml',
        # 'wizard/mrp_workorder_tracking_wizard_views.xml',

        'views/menus.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
