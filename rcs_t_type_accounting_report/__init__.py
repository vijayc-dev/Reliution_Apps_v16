from . import models

from odoo import api, SUPERUSER_ID

def update_chart_of_accounts(env):
    # Fetch all account types and chart of accounts
    account_types = env['account.account.type'].search([])
    chart_of_accounts = env['account.account'].search([])

    # Define a mapping between account type names and selection field values
    account_type_mapping = {
        "asset_receivable": "Receivable",
        "asset_cash": "Bank and Cash",
        "asset_current": "Current Assets",
        "asset_non_current": "Non-current Assets",
        "asset_prepayments": "Prepayments",
        "asset_fixed": "Fixed Assets",
        "liability_payable": "Payable",
        "liability_credit_card": "Credit Card",
        "liability_current": "Current Liabilities",
        "liability_non_current": "Non-current Liabilities",
        "equity": "Equity",
        "equity_unaffected": "Current Year Earnings",
        "income": "Income",
        "income_other": "Other Income",
        "expense": "Expenses",
        "expense_depreciation": "Depreciation",
        "expense_direct_cost": "Cost of Revenue",
        "off_balance": "Off-Balance Sheet"
    }

    # Iterate through the chart of accounts and update the account_type field based on matching account type name
    for account in chart_of_accounts:
        # Find a matching account type by name
        matching_account_type = account_types.filtered(
            lambda a_type: a_type.name == account_type_mapping.get(account.account_type))
        account.sudo().write({'type': matching_account_type[0].id})
