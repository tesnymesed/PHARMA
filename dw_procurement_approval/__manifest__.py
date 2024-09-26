# -*- coding: utf-8 -*-
{
    'name': 'Supplier approval',
    'version': '1.0.0',
    'category': 'Localization',
    'description': """
=        """,
    'author': 'DIGIWAVES - ALGERIA',
    'website': 'www.digiwaves.io',
    'depends': ['dw_supplier_approval'],
    'data': [
        # data
        'data/documents_data.xml',
        'data/sequence.xml',

        # report

        # security
        'security/ir.model.access.csv',
        # views
        'views/procurement_market_views.xml',
        'views/purchase_order_views.xml',
        'views/procurement_consultations_views.xml',
        # menus
        'menus.xml',

        # wizard
        'wizard/dw_market_assign_view.xml',
    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
