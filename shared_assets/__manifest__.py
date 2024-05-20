# -*- coding: utf-8 -*-
{
    'name': 'Shared Assets',
    'version': '1.0',
    'category': 'Tools',
    'author': 'DIGIWAVES - ALGERIA',
    'website': 'www.digiwaves.io',
    'depends': [
        'web'
    ],

    'assets': {
        'web.assets_backend': [
            'shared_assets/static/lib/js/jquery.min.js',
            'shared_assets/static/lib/js/bootstrap.bundle.min.js',
            'shared_assets/static/lib/js/popper.min.js',
            'shared_assets/static/lib/js/bootstrap.min.js',
            'shared_assets/static/lib/js/bootstrap-datepicker.js',
            'shared_assets/static/lib/js/d3-collection.min.js',
            'shared_assets/static/lib/js/tabulator.min.js',
            'shared_assets/static/lib/js/select2.min.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
