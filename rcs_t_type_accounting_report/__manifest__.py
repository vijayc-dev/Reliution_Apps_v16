# -*- coding: utf-8 -*-
{
    'name': 'T-Type Accounting Report for Odoo',

    'summary': """Easy Create profit loss and balance sheet report.Odoo accounting, Odoo accounting software, Odoo bookkeeping, Odoo QuickBooks, Odoo finance,
            Balance sheet, Balance sheet templates, P&L sheet, Business balance sheet, Balance sheet assets, Accounting sheets,
            T-type report, T-format ledger, Debit credit report, General ledger T-account, Double-entry report, Financial report T-style""",

    'description': """
            This module will allow you profit loss and balance sheet report same as Tally structure.Odoo accounting, Odoo accounting software, Odoo bookkeeping, Odoo QuickBooks, Odoo finance,
            Balance sheet, Balance sheet templates, P&L sheet, Business balance sheet, Balance sheet assets, Accounting sheets,
            T-type report, T-format ledger, Debit credit report, General ledger T-account, Double-entry report, Financial report T-style""",

    'category': 'Accounting/Accounting',
    'version': '18.0.0.1.0',
    'license': 'AGPL-3',
    'author': "Reliution",
    'support': 'info@reliution.com',
    'website': "https://www.reliution.com/",
    'images': ["static/description/banner.gif"],

    'depends': ['account'],

    'data': [
        'security/ir.model.access.csv',
        'data/data_account_type.xml',
        'views/profit_loss_menu.xml',
        'views/account_account_view.xml'
    ],

    'assets': {
        'web.assets_backend': [
            'web/static/lib/jquery/jquery.js',
            'rcs_t_type_accounting_report/static/src/css/select2.min.css',
            'rcs_t_type_accounting_report/static/src/xml/**/*',
            'rcs_t_type_accounting_report/static/src/js/**/*',
        ],
        'web.assets_qweb': [
            'rcs_t_type_accounting_report/static/src/xml/**/*',
        ],
    },

    'price': '100',
    'currency': 'USD',
    'installable': True,
    'auto_install': False,
    'application': True,
    'post_init_hook': 'update_chart_of_accounts',
}
