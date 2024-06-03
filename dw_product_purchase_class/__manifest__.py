# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'DW Product Purchase Class',
    'description': 'Define Product Purchase Frequency classes',
    'version': '17.0',
    'sequence': 120,
    'author': 'DIGIWAVES - ALGERIA',
    'website': 'www.digiwaves.io',
    'depends': ['product'],
    'images': [
        'static/description/icon.png'
    ],
    'data': [
        'security/ir.model.access.csv',

        'views/product_views.xml',
        'views/product_purchase_class_views.xml',
        'views/menus.xml',
    ],
    'application': False,
    'installable': True,
    'license': 'LGPL-3',
}
