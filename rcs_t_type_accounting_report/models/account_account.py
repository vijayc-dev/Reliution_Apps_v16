from odoo import models, fields, api, _


class AccountAccount(models.Model):
    _inherit = "account.account"

    chart_of_account_type = fields.Selection(
        [
            ('retained_earning', 'Retained Earning'),
            ('profit_loss', 'Profit Loss'),
            ('defaults', 'Default'),
            ('branch_control', 'Branch Control')
        ])

    type = fields.Many2one(
        "account.account.type",
        string="Account Type"
    )

    def get_account_view(self, output):
        branch_list_new = []
        report_values = self.env['dynamic.accounting.report'].search(
            [('id', '=', self.id)]
        )

        data = {
            'report_type': report_values.report_type,
            'model': self,
        }

        if output.get('date_to'):
            data.update({
                'date_to': output.get('date_to'),
            })
        if output.get('date_from'):
            data.update({
                'date_from': output.get('date_from'),
            })
        if output.get('tax_added'):
            data.update({
                'tax_added': output.get('tax_added'),
            })
        if output.get('branch_list'):
            branch_list_new = list(map(int, output.get('branch_list')))
            data.update({
                'branch_list': branch_list_new,
            })
        # return action
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_account_moves_all")
        action["name"] = 'Journal Items'

        domain = [('account_id', 'in', self.ids), ]
        if output.get('date_from'):
            domain.append(('date', '>=', output['date_from']))
        if output.get('date_to'):
            domain.append(('date', '<=', output['date_to']))
        if output.get('tax_added'):
            domain.append(('tax_ids', '!=',False))
            
        action['domain'] = domain
        action["context"] = {
            'default_account_id': self.ids[0] if self.ids else False,  # Set the first account_id as default
        }
        action['view_mode'] = 'tree,form'

        return action

    def get_account_view_balance_sheet(self, output):
        branch_list_new = []
        report_values = self.env['dynamic.accounting.report'].sudo().search(
            [('id', '=', self.id)]
        )
        data = {
            'report_type': report_values.report_type,
            'model': self,
        }

        if output.get('date_to'):
            data.update({
                'date_to': output.get('date_to'),
            })
        if output.get('date_from'):
            data.update({
                'date_from': output.get('date_from'),
            })

        if output.get('branch_list'):
            branch_list_new = list(map(int, output.get('branch_list')))
            data.update({
                'branch_list': branch_list_new,
            })

        # return action
        action = self.env["ir.actions.actions"].sudo()._for_xml_id("account.action_account_moves_all")
        action["name"] = 'Journal Items'
        domain = [('account_id', 'in', self.ids), ]
        if output.get('date_from'):
            domain.append(('date', '>=', output['date_from']))
        if output.get('date_to'):
            domain.append(('date', '<=', output['date_to']))


        action['domain'] = domain
        action["context"] = {
            'default_account_id': self.ids[0] if self.ids else False,  # Set the first account_id as default
        }
        action['view_mode'] = 'tree,form'

        return action


class AccountAccountType(models.Model):
    _name = "account.account.type"
    _description = "Account Type"

    name = fields.Char(string='Account Type', required=True, translate=True)

    type = fields.Selection([
        ('other', 'Regular'),
        ('receivable', 'Receivable'),
        ('payable', 'Payable'),
        ('liquidity', 'Liquidity'),
    ], required=True, default='other',
        help="The 'Internal Type' is used for features available on " \
             "different types of accounts: liquidity type is for cash or bank accounts" \
             ", payable/receivable is for vendor/customer accounts.")
    internal_group = fields.Selection([
        ('equity', 'Equity'),
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('off_balance', 'Off Balance'),
    ], string="Internal Group",
        help="The 'Internal Group' is used to filter accounts based on the internal group set on the account type.")
    parent_id = fields.Many2one("account.account.type", string="Parent")
    child_ids = fields.One2many('account.account.type', 'parent_id', string="Children")
    level = fields.Integer(string="Level")
    include_initial_balance = fields.Boolean(string="Bring Accounts Balance Forward",
                                             help="Used in reports to know if we should consider journal items from the beginning of time instead of from the fiscal year only. Account types that should be reset to zero at each new fiscal year (like expenses, revenue..) should not have this option set.")
    note = fields.Text(string='Description')

    @api.onchange('parent_id')
    def update_level_in_account(self):
        for record in self:
            level = 0
            parent = record.parent_id
            while parent:
                level += 1
                parent = parent.parent_id
            record.level = level
