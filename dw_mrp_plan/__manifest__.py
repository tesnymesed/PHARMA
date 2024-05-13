# -*- coding: utf-8 -*-
{
    'name': 'MRP  Plan',
    'version': '1.0.0',
    'category': 'Localization',
    'description': """
=        """,
    'author': 'DIGIWAVES - ALGERIA',
    'website': 'www.digiwaves.io',
    'depends': [
        'mrp',
        'mrp_mps'
    ],
    'data': [
        # data
        'data/sequence.xml',
        # report
        'report/mrp_plan_report.xml',

        # security
        'security/ir.model.access.csv',
        'security/security.xml',
        # views
        'views/mrp_plan_view.xml',
        'views/mrp_roadmap_view.xml',
        'views/product_category.xml',
        'views/res_config_settings_views.xml',
        'views/mainDashboard.xml',
        # wizard
        'wizard/roadmap_wizard_views.xml',

        'menus.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'static/src/js/ListController.js',
            'static/src/xml/monthly_mrp_plan_widget_button.xml',
            'dw_mrp_plan/static/src/components/tab/main_dashboard.js',
            'dw_mrp_plan/static/src/components/tab/main_dashboard.xml',
            'dw_mrp_plan/static/src/js/jquery.min.js',
            'dw_mrp_plan/static/src/js/bootstrap.bundle.min.js',
            'dw_mrp_plan/static/src/js/popper.min.js',
            'dw_mrp_plan/static/src/js/bootstrap.min.js',
            'dw_mrp_plan/static/src/js/d3-collection.min.js',
            'dw_mrp_plan/static/src/js/tabulator.min.js',
            'dw_mrp_plan/static/src/js/select2.min.js',
            'dw_mrp_plan/static/src/js/bootstrap-datepicker.js'
        ],
    },



    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
