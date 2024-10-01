# -*- encoding: utf-8 -*-

{
    'name': 'DW Master Production Schedule Link to DW MRP Supply Plan',
    'version': '1.0',
    'category': 'Manufacturing/Manufacturing',
    'sequence': 55,
    'description': """ DW Master Production Schedule Link to DW MRP Supply Plan""",
    'summary': 'DW Master Production Schedule Link to DW MRP Supply Plan',
    'author': 'DIGIWAVES - ALGERIA',
    'website': 'www.digiwaves.io',
    'depends': ['dw_mrp_mps', 'dw_mrp_supply_plan'],

    'assets': {
        'web.assets_backend': [
            'dw_mrp_mps_supply_plan_link/static/src/components/main.xml',
            'dw_mrp_mps_supply_plan_link/static/src/components/main_patch.js',
            'dw_mrp_mps_supply_plan_link/static/src/models/master_production_schedule_model_patch.js',

            # 'dw_mrp_mps/static/src/**/*',
            # 'dw_mrp_mps/static/src/**/*',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',

}
