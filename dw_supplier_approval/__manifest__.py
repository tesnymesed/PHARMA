# -*- coding: utf-8 -*-
{
    'name': 'Supplier approval',
    'version': '1.0.0',
    'category': 'Localization',
    'description': """
=        """,
    'author': 'DIGIWAVES - ALGERIA',
    'website': 'www.digiwaves.io',
    'depends': ['purchase'],
    'data': [
        # data
        'data/documents_data.xml',
        'data/sequence.xml',

        # report

        # security
        'security/security.xml',
        'security/ir.model.access.csv',
        # views
        'views/product_views_inherit.xml',
        'views/procurement_supplier_approval_views.xml',
        'views/res_partner_views.xml',
        # menus
        'menus.xml',

        # wizard
        'wizard/document_wizard.xml',




    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
