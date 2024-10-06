# -*- coding: utf-8 -*-
{
    'name': 'Quality Lot Process',
    'version': '1.0.0',
    'category': 'Quality',
    'description': """
=        """,
    'author': 'DIGIWAVES - ALGERIA',
    'website': 'www.digiwaves.io',
    'depends': [
       'dw_quality_control','dw_location_transfer_limit'
    ],
    'data': [
        #data

        #security
        'security/security.xml',
        #report
        #view
        'views/stock_lo_views.xml',
        'views/product_product_views.xml',
        #menu
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
