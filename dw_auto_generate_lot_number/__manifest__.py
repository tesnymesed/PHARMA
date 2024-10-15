# -*- coding: utf-8 -*-
{
    'name': 'Product',
    'version': '1.0.0',
    'category': 'Localization',
    'description': """
=        """,
    'author': 'DIGIWAVES - ALGERIA',
    'website': 'www.digiwaves.io',
    'depends': ['stock'],
    'data': [
        # data
        # report
        # security
        'security/ir.model.access.csv',
        # views
        'views/product.xml',
    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'license': 'LGPL-3',
}
