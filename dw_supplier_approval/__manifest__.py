# -*- coding: utf-8 -*-
{
    'name': 'Supplier Approval',
    'version': '1.0.0',
    'category': 'Localization',
    'description': """
=        """,
    'author': 'DIGIWAVES - ALGERIA',
    'website': 'www.digiwaves.io',
    'depends': ['base',
      'project','purchase','documents'
    ],
    'data': [
        # data
     'data/documents_data.xml',
        # report

        # security
           'security/ir.model.access.csv',
            'security/security.xml',
        # views

        'views/product.xml',
        'views/homologation.xml',
        'views/market.xml',
        'menus.xml',
        # 'views/assets.xml',

        # wizard
             'wizard/document_wizard.xml',


    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'license': 'LGPL-3',
}
