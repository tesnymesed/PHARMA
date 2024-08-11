# -*- coding: utf-8 -*-
{
    'name': 'Payment request',
    'version': '17.0',
    'category': 'Localization',
    'description': """
=        """,
    'author': 'DIGIWAVES - ALGERIA',
    'website': 'www.digiwaves.io',
    'depends': ['account'],
    'data': [
        # data
'data/souche.xml',
        # report
'report/payment_request_report.xml',
        # security
    'security/ir.model.access.csv',
    'security/security.xml',
        # views
'views/dw_payment_request_view.xml',
'views/dw_reject_reason.xml',

        # menus

'menu.xml',
        # wizard

'wizard/reject_reason.xml'
    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'license': 'LGPL-3',
}
