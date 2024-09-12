# -*- coding: utf-8 -*-
{
    'name': 'Procurement',
    'version': '1.0.0',
    'category': 'Localization',
    'description': """
=        """,
    'author': 'DIGIWAVES - ALGERIA',
    'website': 'www.digiwaves.io',
    'depends': ['dw_base', 'dw_pharma_base', 'purchase_requisition', 'documents'],
    'data': [
        # data
        'data/documents_data.xml',
        'data/sequence.xml',
        'data/market_type_data.xml',
        'data/consultation_crietria_data.xml',
        # report
        # security
        'security/security.xml',
        'security/ir.model.access.csv',
        # views
        'views/market.xml',
        'views/market_type_views.xml',
        'views/dw_consultation_criteria.xml',
        'views/dw_consultations_views.xml',
        'views/dw_consultation_criteria_line.xml',
        'views/procurement_reject_cancel_reason_views.xml',
        # wizard
        'wizard/document_market_wizard.xml',
        'wizard/dw_attribute_market_views.xml',
        # menus
        'menus.xml',

    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
