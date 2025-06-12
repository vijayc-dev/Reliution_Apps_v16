odoo.define('rcs_t_type_accounting_report.ProfitLossReport', function(require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var Dialog = require('web.Dialog');
    var session = require('web.session');
    var _t = core._t;
    var QWeb = core.qweb;
    var ProfitLossReport = AbstractAction.extend({
        contentTemplate: 'ProfitLossReportTemp',
        events: {
            'click .xlsx_profit_loss': 'print_xlsx',
            'click .apply_profit_loss': 'load',
            'change #many2many-select': 'onBranchSelect',
            'click .click_account_line': 'onClickOpenAccount',
        },

        init: function(parent, action) {
            this._super.apply(this, arguments);
            this.selected_branches = [];
            this.branch_list = [];
            this.report_lines = action.report_lines;
            this.wizard_id = action.context.wizard || null;
            this.actionReportId = action.id;
        },

        start: async function() {
            debugger;
            var self = this;
            await this._super.apply(this, arguments);
            this.branch_list = await this.loadBranch();
            self.session = session;
            const option = this.loadReportOptions();
            this.$(".date_from").val(option.pl_sheet_date_from);
            this.$(".date_to").val(option.pl_sheet_date_to);
            if (option.pl_sheet_companies && option.pl_sheet_companies.length > 0) {
                this.selected_branches = option.pl_sheet_companies.map(id =>
                    this.branch_list.find(branch => branch.id == id)
                ).filter(Boolean);
            }

            if (option.pl_sheet_tax_added) {
                this.$("#with_tax_data")[0].checked = true;
            }
            this.load(true);

        },
        loadBranch: async function() {
            debugger;
            const branches = await rpc.query({
                model: 'res.company',
                method: 'search_read',
                args: [
                    [
                        ['id', 'in', session.user_context.allowed_company_ids]
                    ],
                    ['name']
                ],
            });
            return branches;
        },

        print_xlsx: async function() {
            const output = {
                date_range: false
            };
            output.date_from = this.$(".date_from").val();
            output.date_to = this.$(".date_to").val();
            output.branch_list = (this.selected_branches || []).map(branch => branch.id);
            // if the company not selected then default company is current login company
            if (output.branch_list.length <= 0) {
                output.branch_list = [].concat(session.user_context.allowed_company_ids[0]);
            }
            output.tax_added = this.$("#with_tax_data").is(":checked");
            try {
                const datas = await rpc.query({
                    model: 'dynamic.accounting.report',
                    method: 'action_xlsx',
                    args: [
                        [this.wizard_id], output
                    ],
                });
                this.do_action(datas);
            } catch (error) {
                console.error('Error opening account view:', error);
            }
        },

        sessionOptionsID: function() {
            return `rcs_t_type_accounting_report:${this.actionReportId}:${session.user_companies.current_company}`;
        },

        saveSessionOptions: function(options) {
            sessionStorage.setItem(this.sessionOptionsID(), JSON.stringify(options));
        },

        sessionOptions: function() {
            return JSON.parse(sessionStorage.getItem(this.sessionOptionsID())) || {};
        },

        loadReportOptions: function() {
            const loadOptions = this.sessionOptions();
            if (Object.keys(loadOptions).length === 0) {
                const now = new Date();
                const year = now.getFullYear();
                const isAfterMarch = now.getMonth() >= 3;

                const fyStart = new Date(isAfterMarch ? year : year - 1, 3, 1);
                const fyEnd = new Date(isAfterMarch ? year + 1 : year, 2, 31);
                const formatDate = (date) =>
                    `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;

                loadOptions.pl_sheet_date_from = formatDate(fyStart);
                loadOptions.pl_sheet_date_to = formatDate(fyEnd);
                loadOptions.pl_sheet_companies = loadOptions.pl_sheet_companies || [];
                loadOptions.pl_sheet_tax_added = loadOptions.pl_sheet_tax_added || false;

            }

            return loadOptions;
        },

        onClickOpenAccount: async function(ev) {
            const output = {
                date_range: false
            };
            output.date_from = this.$(".date_from").val();
            output.date_to = this.$(".date_to").val();
            output.branch_list = (this.selected_branches || []).map(branch => branch.id);
            // if the company not selected then default company is current login company
            if (output.branch_list.length <= 0) {
                output.branch_list = [].concat(session.user_context.allowed_company_ids[0]);
            }
            output.tax_added = this.$("#with_tax_data")[0]?.checked || false;

            // Save filters to localStorage before navigating
            sessionStorage.setItem('from_navigation', '1'); // Mark that user is navigating
            localStorage.setItem('accounting_report_filters', JSON.stringify(output));

            const account_id = parseInt(ev.currentTarget.id);
            try {
                const datas = await rpc.query({
                    model: 'account.account',
                    method: 'get_account_view',
                    args: [
                        [account_id], output
                    ],
                });
                this.do_action(datas);
            } catch (error) {
                console.error('Error opening account view:', error);
            }
        },
        // Select the Companies and store in selected_branches list
        onBranchSelect: function(ev) {
            const selectedOptions = [].concat($(ev.currentTarget).val());
            this.selected_branches = selectedOptions.map(id =>
                this.branch_list.find(branch => branch.id == id)
            ).filter(Boolean);
        },

        load: async function() {
            debugger;
            let output = {
                date_range: false
            };
            let save_options = {};
            //           Same as        const date_to = document.querySelector(".date_to").value;
            const date_from = this.$(".date_from")[0];
            const date_to = this.$(".date_to")[0];

            if (this.$(".date_from")[0]) {
                output.date_from = this.$(".date_from")[0].value;
                save_options.pl_sheet_date_from = this.$(".date_from")[0].value;
            }
            if (this.$(".date_to")[0]) {
                output.date_to = this.$(".date_to")[0].value;
                save_options.pl_sheet_date_to = this.$(".date_to")[0].value;
            }
            if (Object.keys(save_options).length === 0) {
                console.log("log")
                save_options = this.loadReportOptions();
            }
            if (this.$("#with_tax_data")[0]) {
                output.tax_added = this.$("#with_tax_data")[0].checked;
                save_options.pl_sheet_tax_added = this.$("#with_tax_data")[0]?.checked;
            }
            if (this.selected_branches.length) {
                save_options.pl_sheet_companies = this.selected_branches.map(b => b.id);
            }
            // store the data in session FromDate, ToDate, TaxData and Company
            this.saveSessionOptions(save_options);
            if (Object.keys(output).length === 0) {
                output = {
                    'date_from': save_options.pl_sheet_date_from,
                    'date_to': save_options.pl_sheet_date_to,
                    'tax_added': save_options.pl_sheet_tax_added
                }
            }
            output.branch_list = (this.selected_branches || []).map(branch => branch.id)
            // if the company not selected then default company is current login company
            if (output.branch_list.length <= 0) {
                output.branch_list = [].concat(session.user_context.allowed_company_ids[0]);
            }

            //Pass out the Branch List in xml
            this.$('.custom_companies_options').html(QWeb.render(
                'CustomBranchList', {
                    branch_list: this.branch_list,
                }
            ));
            // Set the default company as a SelectBox
            this.$('#many2many-select').val(output.branch_list);

            //  Call python method to prepare the reports data
            try {
                const datas = await rpc.query({
                    model: 'dynamic.accounting.report',
                    method: 'purchase_report',
                    args: [
                        [this.wizard_id], output
                    ],
                });
                if (datas.orders) {
                    console.log("datas.orders have a data");
                    this.$('.table_view_pr').html(QWeb.render(
                        'FinanceTableCustom', {
                            filter: datas.filters,
                            order: datas.orders,
                            income_lines: datas.report_lines.income_lines,
                            expense_lines: datas.report_lines.expense_lines,
                            net_lines: datas.report_lines.net_profit
                        }
                    ));
                }
            } catch (error) {
                console.error('Error loading data:', error);
            }
        },
    });
    core.action_registry.add('profitLossReport', ProfitLossReport);
    return ProfitLossReport;
});