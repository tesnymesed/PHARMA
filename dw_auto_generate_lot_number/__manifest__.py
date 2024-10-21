# -*- coding: utf-8 -*-
{
    'name': 'Product',
    'version': '1.0.0',
    'category': 'Localization',
    'description': """
=        """,
    'author': 'DIGIWAVES - ALGERIA',
    'website': 'www.digiwaves.io',
    'depends': ['stock', 'dw_pharma_base'],
    'data': [
        # data
        # report
        # security
        'security/ir.model.access.csv',
        # views
        'views/product_template.xml',
        'views/product_pharmaceutical_family.xml',
    ],
    'qweb': [

    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
