# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'DW Master Production Schedule',
    'version': '1.0',
    'category': 'Manufacturing/Manufacturing',
    'sequence': 50,
    'description': """ DW Master Production Schedule """,
    'summary': 'DW Master Production Schedule',
    'author': 'DIGIWAVES - ALGERIA',
    'website': 'www.digiwaves.io',
    'depends': ['mrp_mps'],
    'data': [
        'views/res_config_settings_views.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'dw_mrp_mps/static/src/components/line_patch.js'
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',

}
