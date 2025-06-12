import json
import io
import base64
import xlwt
import pytz
import platform
from odoo import models, api, _, fields
from collections import defaultdict
from datetime import datetime, date


class DynamicPurchaseReport(models.Model):
    _name = "dynamic.accounting.report"
    _description = "Dynamic Accounting Report"

    purchase_report = fields.Char(
        string="Purchase Report"
    )

    date_from = fields.Datetime(
        string="Date From"
    )

    date_to = fields.Datetime(
        string="Date to"
    )

    report_type = fields.Selection(
        [
            ('report_by_order', 'Report By Order'),
            ('report_by_order_detail', 'Report By Order Detail'),
            ('report_by_product', 'Report By Product'),
            ('report_by_categories', 'Report By Categories'),
            ('report_by_purchase_representative', 'Report By Purchase Representative'),
            ('repot_by_state', 'Report By State')],

        default='report_by_order'
    )
    branch_ids = fields.Many2many('res.company')

    @api.model
    def purchase_report(self, option, output={}):
        report_values = self.env['dynamic.accounting.report'].search(
            [('id', '=', option[0])])
        data = {
            'report_type': report_values.report_type,
            'model': self,
        }
        if output.get('date_from'):
            data.update({
                'date_from': output.get('date_from')
            })
        if output.get('date_to'):
            data.update({
                'date_to': output.get('date_to'),
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
        filters = self.get_filter(option)
        lines = self._get_report_values(data)
        return {
            'name': "Purchase Orders",
            'type': 'ir.actions.client',
            'tag': 's_r',
            'orders': data,
            'filters': filters,
            'report_lines': lines,
        }

    def balance_get_filter(self, report_values):
        filter_dict = {
            'date_from': self.date_from,
            'date_to': self.date_to,

        }
        return filter_dict

    def get_filter(self, report_values):
        filter_dict = {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }
        return filter_dict

    @api.model
    def _get_report_values(self, docids, data=None):
        income_lines = self._get_account_move_lines('income', data=docids)
        expense_lines = self._get_account_move_lines('expense', data=docids)
        new_income_line = self.sum_of_same_income_expense_account(income_lines)
        new_expense_line = self.sum_of_same_income_expense_account(expense_lines)
        grouped_income_lines = self.group_by_account_type(new_income_line)
        grouped_expense_lines = self.group_by_account_type(new_expense_line)
        net_profit = self.prepare_net_profit(new_income_line, new_expense_line)
        return {
            'doc_ids': docids,
            'doc_model': 'account.move.line',
            'income_lines': grouped_income_lines,
            'expense_lines': grouped_expense_lines,
            'net_profit': net_profit
        }

    def prepare_net_profit(self, income_line, expense_line):
        total_income = abs(sum(entry['amount'] for entry in income_line.values()))
        total_expense = abs(sum(entry['amount'] for entry in expense_line.values()))
        total_profit = total_income - total_expense
        return {
            'total_amount': total_profit,
            'total_income': total_income,
            'total_expense': total_expense,
            'profit_loss': 'profit' if total_profit > 0 else 'loss'
        }

    def sum_of_same_income_expense_account(self, income_lines):
        sums_dict = {}
        # Calculate the sum of amounts for each account ID
        for item in income_lines:
            account_id = item['account_id']
            amount = item['amount']
            if account_id not in sums_dict:
                sums_dict[account_id] = item.copy()
                sums_dict[account_id]['amount'] = round(amount, 2)
            else:
                sums_dict[account_id]['amount'] += amount
                sums_dict[account_id]['amount'] = round(sums_dict[account_id]['amount'], 2)
        return sums_dict

    def group_by_account_type(self, records):
        grouped = defaultdict(list)
        for record in records.values():
            grouped[record['account_type']].append(record)
        return grouped

    def group_by_account_type_balance_sheet(self, records):  # Fetch all records
        grouped_data = defaultdict(lambda: defaultdict(list))
        account_type_model = self.env['account.account.type']

        for record in records.values():
            account_type = record['account_type']
            parent_id = record.get('parent_id')

            # Start with the current record and move up the hierarchy to find the root parent
            parent_id_search = account_type_model.browse(parent_id).exists() if parent_id else None
            while parent_id_search and parent_id_search.parent_id:
                parent_id_search = parent_id_search.parent_id

            if parent_id_search:
                # Group data under the correct parent node
                root_parent_name = parent_id_search.name
            else:
                # If no parent found, use the current record's name as the root
                root_parent_name = record['parent_name']
            if not root_parent_name:
                root_parent_name = ''
            grouped_data[root_parent_name][account_type].append(record)

        return grouped_data

    def _get_account_move_lines(self, account_type, data=None):
        # Fetch the account type
        account_list = []
        account_type_ids = self.env['account.account.type'].search([('internal_group', '=', account_type)])
        for account_type_id in account_type_ids:
            # Fetch account move lines for the specified account type
            if data.get('date_from') and data.get('date_to'):
                from_date = datetime.strptime(data.get('date_from'), '%Y-%m-%d').date()
                to_date = datetime.strptime(data.get('date_to'), '%Y-%m-%d').date()
                if data.get('tax_added'):
                    lines = self.env['account.move.line'].sudo().search(
                        [('account_id.type', '=', account_type_id.id), ('date', '<=', to_date),
                         ('date', '>=', from_date), ('tax_ids', '!=', False)])
                else:
                    lines = self.env['account.move.line'].sudo().search(
                        [('account_id.type', '=', account_type_id.id), ('date', '<=', to_date),
                         ('date', '>=', from_date)])
            elif data.get('date_to'):
                to_date = datetime.strptime(data.get('date_to'), '%Y-%m-%d').date()
                if data.get('tax_added'):
                    lines = self.env['account.move.line'].sudo().search(
                        [('account_id.type', '=', account_type_id.id), ('date', '<=', to_date),
                         ('tax_ids', '!=', False)])
                else:
                    lines = self.env['account.move.line'].sudo().search(
                        [('account_id.type', '=', account_type_id.id), ('date', '<=', to_date),
                         ])
            else:
                if data.get('tax_added'):
                    lines = self.env['account.move.line'].sudo().search(
                        [('account_id.type', '=', account_type_id.id), ('tax_ids', '!=', False)])
                else:
                    lines = self.env['account.move.line'].sudo().search(
                        [('account_id.type', '=', account_type_id.id)])
            if data.get('branch_list'):
                lines = lines.sudo().filtered(
                    lambda line: line.company_id.id in data.get('branch_list') and line.parent_state == 'posted')
            else:
                lines = lines.filtered(
                    lambda line: line.parent_state == 'posted')
            account_list.extend([
                {'date': line.date,
                 'account_id': line.account_id.id,
                 'account_name': line.account_id.name,
                 'account_type': account_type_id.name,
                 'level': account_type_id.level,
                 'chart_of_account_type': line.account_id.chart_of_account_type,
                 'parent_id': account_type_id.parent_id.id,
                 'parent_name': account_type_id.parent_id.name,
                 'account_code': line.account_id.code,
                 'amount': (line.credit - line.debit)} for line in
                lines])
        return account_list

    def balance_sheet_report(self, output, option={}):
        report_values = self.env['dynamic.accounting.report'].search(
            [('id', '=', self.id)])
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
        filters = self.balance_get_filter(output)
        lines = self._get_balance_sheet_report_values(data)
        return {
            'name': "Balance Sheet",
            'type': 'ir.actions.client',
            'tag': 's_r',
            'orders': data,
            'filters': filters,
            'report_lines': lines,
        }

    def balance_action_xlsx(self, output={}):
        ''' Button function for Xlsx '''
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('Balance Sheet')
        font_size = 5
        report_values = self.env['dynamic.accounting.report'].search(
            [('id', '=', self.id)])
        report_data = {
            'report_type': report_values.report_type,
            'model': self,
        }
        if output.get('date_to'):
            report_data.update({
                'date_to': output.get('date_to'),
            })
        if output.get('date_from'):
            report_data.update({
                'date_from': output.get('date_from'),
            })
        if output.get('branch_list'):
            branch_list_new = list(map(int, output.get('branch_list')))
            report_data.update({
                'branch_list': branch_list_new,
            })
        data = self._get_balance_sheet_report_values(report_data)
        ist = pytz.timezone('Asia/Kolkata')

        xlwt.add_palette_colour("light_grey", 0x16)
        workbook.set_colour_RGB(0x16, 128, 128, 128)

        style1 = xlwt.easyxf(
            'font:bold True; borders:left thin, right thin, top thin, bottom thin;align: horiz center; pattern: pattern solid,fore_colour light_grey;',
            num_format_str='#,##0.00')
        style2 = xlwt.easyxf(
            f'font:bold True, height {font_size * 55}; borders:left thin, right thin, top thin, bottom thin;align: horiz center, vert center;'
            f'pattern: pattern solid,fore_colour light_grey;', num_format_str='#,##0.00')
        style3 = xlwt.easyxf(
            f'font:bold True; borders:left thin, right thin, top thin, bottom thin;align: horiz center, vert center;'
            f'pattern: pattern solid,fore_colour light_grey;', num_format_str='#,##0.00')
        style4 = xlwt.easyxf(f'align: horiz left;', num_format_str='#,##0.00')
        style5 = xlwt.easyxf(
            f'font:bold True; align: horiz center, vert center;',
            num_format_str='#,##0.00')
        style6 = xlwt.easyxf(f'align: horiz right;', num_format_str='#,##0.00')

        sheet.write_merge(0, 0, 0, 8, 'Balance Sheet- T Format', style2)
        col = 0

        sheet.write(3, col, 'Search Criteria:', style3)
        sheet.write(4, col, 'Accounting Site:', style4)
        if len(output['branch_list']) > 0:
            branches = []
            for branch in data['doc_ids']['branch_list']:
                branches.append(self.env['res.company'].browse(int(branch)).name)
            sheet.write(4, 1, branches, style4)
        else:
            sheet.write(4, 1, 'ALL', style4)
        sheet.write(5, col, 'From Date:', style4)
        sheet.write(5, 1, data['doc_ids'].get('date_from'), style4)
        sheet.write(6, col, 'To Date:', style4)
        sheet.write(6, 1, data['doc_ids'].get('date_to'), style4)

        headers = ['Description', 'Amount', '', '', 'Description', 'Amount', '']

        row = 4
        col = 0
        sheet.col(0).width = int(20 * 260)
        sheet.col(1).width = int(28 * 260)
        sheet.col(2).width = int(20 * 260)
        sheet.col(3).width = int(20 * 260)
        sheet.col(4).width = int(20 * 260)
        sheet.col(5).width = int(20 * 260)
        sheet.col(6).width = int(28 * 260)
        sheet.col(7).width = int(20 * 260)
        sheet.col(8).width = int(20 * 260)
        for col, header in enumerate(headers):
            sheet.write(8, col, header, style1)
            col += 1

        liability_lines = data['liability_lines']
        assets_lines = data['assets_lines']
        equity_line = data['equity_lines']

        col = 0
        row = 9
        exp_row = 10
        inc_row = 10
        sheet.write(row, col, 'LIABILITY', style5)
        style_bold_italic = xlwt.easyxf(
            'font: bold on, italic on; align: horiz center, vert center;'
        )
        style_bold_italic_underline = xlwt.easyxf(
            'font: bold on, italic on, underline on; align: horiz center, vert center;'
        )
        sheet.write(row, col + 1, data.get('total_balance').get('total_liability'), style5)
        row += 1
        for key, value in equity_line.items():
            sheet.write(row, col, key, style_bold_italic)
            key_row = row
            total = 0
            row += 1
            for new_key, rec in value.items():
                sheet.write(row, col, new_key, style_bold_italic_underline)
                row += 1
                for line in rec:
                    # sheet.write(row, col, line['account_code'], style4)
                    sheet.write(row, col, line['account_name'], style4)
                    sheet.write(row, col + 1, line['amount'], style6)
                    # sheet.write(row, col + 3, (rec['amount'] * 100) / total_income, style6)
                    row += 1
                    total += line['amount']
            exp_row = row
            sheet.write(key_row, col + 2, total, style6)
            # sheet.write(key_row, col + 3, (total * 100) / total_income, style6)

        for key, value in liability_lines.items():
            sheet.write(row, col, key, style_bold_italic)
            key_row = row
            total = 0
            row += 1
            for new_key, rec in value.items():
                sheet.write(row, col, new_key, style_bold_italic_underline)
                total = 0
                for line in rec:
                    total += line['amount']
                sheet.write(row, col + 2, total, style6)
                row += 1
                for line in rec:
                    sheet.write(row, col, line['account_name'], style4)
                    sheet.write(row, col + 1, line['amount'], style6)
                    row += 1
            exp_row = row

        col = 4
        row = 9
        sheet.write(row, col, 'ASSETS', style5)
        sheet.write(row, col + 1, data.get('total_balance').get('total_assets'), style5)
        row += 1
        for key, value in assets_lines.items():
            sheet.write(row, col, key, style_bold_italic)
            key_row = row
            row += 1
            for new_key, rec in value.items():
                sheet.write(row, col, new_key, style_bold_italic_underline)
                total = 0
                for line in rec:
                    total += line['amount']
                sheet.write(row, col + 2, total, style6)
                row += 1
                for line in rec:
                    sheet.write(row, col, line['account_name'], style4)
                    sheet.write(row, col + 1, line['amount'], style6)
                    row += 1
        inc_row = row

        col = 0
        if exp_row > inc_row:
            row = exp_row + 1
        else:
            row = inc_row + 1

        balance_total = data.get('total_balance').get('total_liability') - data.get('total_balance').get('total_assets')
        sheet.write(row, col + 0, 'Equity', style3)
        sheet.write(row, col + 1, balance_total, style3)
        sheet.write(row + 2, col, f'Exported on: {datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")}')

        if platform.system() == 'Linux':
            filename = ('/tmp/Balance Sheet Report' + '.xls')
        else:
            filename = ('Balance Sheet Report' + '.xls')

        workbook.save(filename)
        fp = open(filename, "rb")
        file_data = fp.read()
        out = base64.encodebytes(file_data)

        attach_vals = {
            'name': 'Balance Sheet Report.xls',  # Specify the name of the attachment
            'datas': out,  # Specify the binary data of the attachment
            'res_model': 'dynamic.accounting.report',  # Specify the model where the attachment belongs
            'res_id': self.id,  # Specify the ID of the record to which the attachment is attached
        }

        # Create the attachment record
        act_id = self.env['ir.attachment'].create(attach_vals)

        return {
            'name': 'Balance Sheet Report',
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{act_id.id}?download=true',
            'target': 'self',
        }

    @api.model
    def _get_balance_sheet_report_values(self, docids, data=None):
        profit_loss = self._get_report_values(docids)
        total_amount_pl = profit_loss.get('net_profit').get('total_amount')
        liability_lines = self._get_account_move_lines('liability', data=docids)
        assets_lines = self._get_account_move_lines('asset', data=docids)
        equity_lines = self._get_account_move_lines('equity', data=docids)
        new_liability_lines = self.sum_of_same_income_expense_account(liability_lines)
        new_assets_lines = self.sum_of_same_income_expense_account(assets_lines)
        new_equity_lines = self.sum_of_same_income_expense_account(equity_lines)
        grouped_liability_lines = self.group_by_account_type_balance_sheet(new_liability_lines)
        grouped_assets_lines = self.group_by_account_type_balance_sheet(new_assets_lines)
        grouped_equity_lines = self.group_by_account_type_balance_sheet(new_equity_lines)
        net_liability_assets = self.prepare_net_liability_assets(new_liability_lines, new_assets_lines, new_equity_lines,
                                                                 total_amount_pl)
        self.update_retained_earning_amount(grouped_liability_lines, total_amount_pl)
        self.update_profit_loss_amount(grouped_liability_lines, total_amount_pl)
        return {
            'doc_ids': docids,
            'doc_model': 'account.move.line',
            'liability_lines': grouped_liability_lines,
            'assets_lines': grouped_assets_lines,
            'equity_lines': grouped_equity_lines,
            'total_balance': net_liability_assets,
            'profit_loss': total_amount_pl
        }

    def update_profit_loss_amount(self, data, total_amount_pl):
        retained_earning_types = []
        for category, subcategories in data.items():
            for account_type, accounts in subcategories.items():
                for account in accounts:
                    if account['chart_of_account_type'] == 'profit_loss':
                        retained_earning_types.append(account['chart_of_account_type'])
                        account.update({'amount': account.get('amount')})

    def update_retained_earning_amount(self, data, total_amount_pl):
        retained_earning_types = []
        for category, subcategories in data.items():
            for account_type, accounts in subcategories.items():
                for account in accounts:
                    if account['account_name'] == 'Retained Earning':
                        retained_earning_types.append(account['chart_of_account_type'])
                        account.update({'amount': account.get('amount') + total_amount_pl})

    def prepare_net_liability_assets(self, liability_line, assets_line, equity_lines, total_amount_pl=0):
        total_liability = abs(sum(entry['amount'] for entry in liability_line.values()))
        total_assets = abs(sum(entry['amount'] for entry in assets_line.values()))
        total_equity = abs(sum(entry['amount'] for entry in equity_lines.values()))
        total_value = total_assets - total_liability

        # Calculate total equity
        total_value_equity = total_liability + total_amount_pl + total_equity
        return {
            'total_amount': (total_value_equity),
            'total_liability': total_liability,
            'total_assets': total_assets,
            'total_equity': total_amount_pl + total_equity,
            'balance_data': 'liability'
        }

    def action_xlsx(self, output={}):
        ''' Button function for Xlsx '''

        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('Profit And Loss')
        font_size = 5
        report_values = self.env['dynamic.accounting.report'].search(
            [('id', '=', self.id)])
        report_data = {
            'report_type': report_values.report_type,
            'model': self,
        }
        if output.get('date_from'):
            report_data.update({
                'date_from': output.get('date_from')
            })
        if output.get('date_to'):
            report_data.update({
                'date_to': output.get('date_to'),
            })
        if output.get('tax_added'):
            report_data.update({
                'tax_added': output.get('tax_added'),
            })
        if output.get('branch_list'):
            branch_list_new = list(map(int, output.get('branch_list')))
            report_data.update({
                'branch_list': branch_list_new,
            })
        data = self._get_report_values(report_data)
        total_income = int(data['net_profit']['total_income'])
        total_expense = int(data['net_profit']['total_expense'])
        profit_loss = total_income - total_expense
        ist = pytz.timezone('Asia/Kolkata')

        xlwt.add_palette_colour("light_grey", 0x16)
        workbook.set_colour_RGB(0x16, 128, 128, 128)

        style1 = xlwt.easyxf(
            'font:bold True; borders:left thin, right thin, top thin, bottom thin;align: horiz center; pattern: pattern solid,fore_colour light_grey;',
            num_format_str='#,##0.00')
        style2 = xlwt.easyxf(
            f'font:bold True, height {font_size * 55}; borders:left thin, right thin, top thin, bottom thin;align: horiz center, vert center;'
            f'pattern: pattern solid,fore_colour light_grey;', num_format_str='#,##0.00')
        style3 = xlwt.easyxf(
            f'font:bold True; borders:left thin, right thin, top thin, bottom thin;align: horiz center, vert center;'
            f'pattern: pattern solid,fore_colour light_grey;', num_format_str='#,##0.00')
        style4 = xlwt.easyxf(f'align: horiz left;', num_format_str='#,##0.00')
        style5 = xlwt.easyxf(
            f'font:bold True; align: horiz center, vert center;',
            num_format_str='#,##0.00')
        style6 = xlwt.easyxf(f'align: horiz right;', num_format_str='#,##0.00')
        style7 = xlwt.easyxf(f'font: height 400; align: horiz center;')

        sheet.write_merge(0, 0, 0, 6, 'Profit And Loss Account - T Format', style2)
        col = 0
        sheet.write(3, col, 'Search Criteria:', style3)
        sheet.write(4, col, 'Accounting Site:', style4)
        if len(output['branch_list']) > 0:
            branches = []
            for branch in data['doc_ids']['branch_list']:
                branches.append(self.env['res.company'].browse(int(branch)).name)
            sheet.write(4, 1, branches, style4)
        else:
            sheet.write(4, 1, 'ALL', style4)
        sheet.write(5, col, 'From Date:', style4)
        sheet.write(5, 1, data['doc_ids'].get('date_from'), style4)
        sheet.write(6, col, 'To Date:', style4)
        sheet.write(6, 1, data['doc_ids'].get('date_to'), style4)

        headers = ['Description', '', 'Amount', '', 'Description', '', 'Amount']

        row = 4
        col = 0
        sheet.col(0).width = int(20 * 260)
        sheet.col(1).width = int(28 * 260)
        sheet.col(2).width = int(20 * 260)
        sheet.col(3).width = int(5 * 260)
        sheet.col(4).width = int(20 * 260)
        sheet.col(5).width = int(28 * 260)
        sheet.col(6).width = int(20 * 260)
        for col, header in enumerate(headers):
            sheet.write(8, col, header, style1)
            col += 1

        sheet.write(7, 1, 'Income', style7)
        sheet.write(7, 5, 'Expense', style7)

        expense_lines = data['expense_lines']
        income_lines = data['income_lines']
        col = 0
        row = 9
        exp_row = 10
        inc_row = 10
        for key, value in income_lines.items():
            sheet.write(row, col, key, style5)
            key_row = row
            total = 0
            for rec in value:
                total += rec['amount']
            sheet.write(key_row, col + 2, total, style6)
            row += 1
            for rec in value:
                # sheet.write(row, col, rec['account_code'], style4)
                sheet.write(row, col, rec['account_name'], style4)
                sheet.write(row, col + 1, '', style4)
                sheet.write(row, col + 2, rec['amount'], style6)
                row += 1
                # total += rec['amount']
            exp_row = row

        col = 4
        row = 9
        for key, value in expense_lines.items():
            sheet.write(row, col, key, style5)
            key_row = row
            total = 0
            for rec in value:
                total += rec['amount']
            sheet.write(key_row, col + 2, total, style6)
            row += 1
            for rec in value:
                # sheet.write(row, col, rec['account_code'], style4)
                sheet.write(row, col, rec['account_name'], style4)
                sheet.write(row, col + 1, '', style4)
                sheet.write(row, col + 2, rec['amount'], style6)
                row += 1
                total += rec['amount']
            inc_row = row

        col = 0
        if exp_row > inc_row:
            row = exp_row + 1
        else:
            row = inc_row + 1

        sheet.write(row, col + 1, '', style3)
        sheet.write(row, col + 3, '', style3)
        sheet.write(row, col + 5, '', style3)

        if data['net_profit']['profit_loss'] == 'profit':
            sheet.write(row, col, 'Net Profit', style3)
            sheet.write(row, col + 2, profit_loss, style3)
            sheet.write(row, col + 6, '', style3)
            sheet.write(row, col + 4, '', style3)
        else:
            sheet.write(row, col, '', style3)
            sheet.write(row, col + 4, 'Net Loss', style3)
            sheet.write(row, col + 6, profit_loss, style3)
            sheet.write(row, col + 2, '', style3)

        sheet.write(row + 2, col, f'Exported on: {datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")}')

        if platform.system() == 'Linux':
            filename = ('/tmp/Profit and Loss Report' + '.xls')
        else:
            filename = ('Profit and Loss Report' + '.xls')

        workbook.save(filename)
        fp = open(filename, "rb")
        file_data = fp.read()
        out = base64.encodebytes(file_data)

        attach_vals = {
            'name': 'Profit Loss Report.xls',  # Specify the name of the attachment
            'datas': out,  # Specify the binary data of the attachment
            'res_model': 'dynamic.accounting.report',  # Specify the model where the attachment belongs
            'res_id': self.id,  # Specify the ID of the record to which the attachment is attached
        }

        # Create the attachment record
        act_id = self.env['ir.attachment'].create(attach_vals)

        return {
            'name': 'Profit Loss Report',
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{act_id.id}?download=true',
            'target': 'self',
        }
