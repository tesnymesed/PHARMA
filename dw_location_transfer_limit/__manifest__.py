# -*- coding: utf-8 -*-
{
    'name': 'Location Transfer Limit',
    'version': '1.0.0',
    'category': 'Inventory',
    'description': """
=        """,
    'author': 'DIGIWAVES - ALGERIA',
    'website': 'www.digiwaves.io',
    'depends': [
       'stock'
    ],
    'data': [
        #data

        #security
        'security/ir.model.access.csv',
        #report
        #view
        'views/stock_location_transfer_limit_views.xml',
        'views/stock_location_inherit.xml',
        #menu
        'menus.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
