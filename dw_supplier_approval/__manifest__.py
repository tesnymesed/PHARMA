# -*- coding: utf-8 -*-
{
    'name': 'Supplier Homologation',
    'version': '1.0.0',
    'category': 'Localization',
    'description': """
=        """,
    'author': 'DIGIWAVES - ALGERIA',
    'website': 'www.digiwaves.io',
    'depends': ['dw_procurement'],
    'data': [
        # data
        'data/documents_data.xml',
        'data/sequence.xml',

        # report

        # security
        'security/security.xml',
        'security/ir.model.access.csv',
        # views
        'views/market.xml',

        'views/product.xml',
        'views/homologation.xml',
        'views/purchase_order_views.xml',
        'views/res_partner_views.xml',
        'views/dw_consultations_views.xml',
        # menus
        'menus.xml',

        # wizard
        'wizard/document_wizard.xml',
        'wizard/dw_market_assign_view.xml',



    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'license': 'LGPL-3',
}
