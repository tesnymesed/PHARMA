{
    'name': 'MRP Alert Decision',
    'version': '17.0.0.1',
    'category': 'Manufacturing',
    'description': """
        This module adds the DW MRP Alert Decision model.
    """,
    'author': 'DIGIWAVES - ALGERIA',
    'website': 'www.digiwaves.io',
    'depends': ['base', 'mrp'],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_alert_decision_views.xml',
    ],
    'images': [
        'static/description/icon.png'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
