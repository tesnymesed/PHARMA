# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'DW Product Quota',
    'version': '17.0',
    'sequence': 120,
    'author': 'DIGIWAVES - ALGERIA',
    'website': 'www.digiwaves.io',
    'depends': ['purchase', 'product'],
    'images': [
        'static/description/icon.png'
    ],
    'data': [
        'security/ir.model.access.csv',

        'views/product_views.xml',
        'views/dw_product_quota.xml',
        'views/dw_product_quota_type.xml',
        'views/menus.xml',
    ],
    'application': False,
    'installable': True,
    'license': 'LGPL-3',
}
