# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Solution Pharma BASE',
    'version': '17.0',
    'sequence': 10,
    'author': 'DIDIWAVES - ALGERIA',
    'website': 'www.digiwaves.io',
    'depends': ['dw_base', 'stock', ],
    'images': ['static/description/icon.png'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/product.xml',
        'views/partner.xml',
        'views/product_pharmaceutical.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
