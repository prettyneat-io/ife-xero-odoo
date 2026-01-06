{
    'name': 'Xero Integration POC',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Proof of Concept for Xero Integration',
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': True,
    'external_dependencies': {
        'python': ['requests'],
    },
}
