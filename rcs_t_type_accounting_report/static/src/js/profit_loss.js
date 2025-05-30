odoo.define('rcs_t_type_accounting_report.ProfitLossReport', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var Session = require('web.session');
    var QWeb = core.qweb;
    var _t = core._t;

    var ProfitLossReport = AbstractAction.extend({
        contentTemplate: 'ProfitLossReportTemp',
        events: {
            'click .xlsx_profit_loss': 'print_xlsx',
            'click .apply_profit_loss': 'loadData',
//            'change #many2many-select': 'onBranchSelect',
//            'change #with_tax_data': 'toggleWithTaxData',
//            'click .click_account_line': 'onClickOpenAccount',
        },

        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.actionReportId = action.id;
            this.report_lines = action.report_lines;
            this.branch_list = [];
            this.wizard_id = action.context.wizard || null;
            this.selected_branches = [];
            debugger;
        },

        start: async function () {
            var self = this;
            await this._super.apply(this, arguments);
            await this.loadBranches();
            self.session= Session;
            const options = this.loadReportOptions();
            this.$('.date_from').val(options.pl_sheet_date_from);
            this.$('.date_to').val(options.pl_sheet_date_to);

            // Initialize Select2
            const $selectBox = this.$('#many2many-select');
            $selectBox.select2({
                placeholder: "Select branches...",
                tags: true,
                width: 'resolve',
            });

            this.loadData(true);
        },

        loadBranches: async function () {
            this.branch_list = await rpc.query({
                model: 'res.company',
                method: 'search_read',
                args: [[], ['name']],
            });
        },

        sessionOptionsID: function () {
            return `rcs_t_type_accounting_report:${this.actionReportId}:${session.user_companies.current_company}`;
        },

        saveSessionOptions: function (options) {
            sessionStorage.setItem(this.sessionOptionsID(), JSON.stringify(options));
        },

        sessionOptions: function () {
            return JSON.parse(sessionStorage.getItem(this.sessionOptionsID())) || {};
        },

        loadReportOptions: function () {
            let loadOptions = this.sessionOptions();
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
            }
            return loadOptions;
        },

        onBranchSelect: function (ev) {
            const selectedIds = $(ev.currentTarget).val();
            this.selected_branches = selectedIds.map(id =>
                this.branch_list.find(branch => branch.id == id)
            ).filter(Boolean);
        },

        toggleWithTaxData: function (ev) {
            // Checkbox handler placeholder
        },

        removeBranch: function (branch_id) {
            this.selected_branches = this.selected_branches.filter(branch => branch.id !== branch_id);
            this.$("#many2many-select").val(this.selected_branches.map(branch => branch.id)).trigger("change");
        },

        loadData: async function () {
            let output = {
                date_range: false
            };
            let save_options = {};
            const dateFrom = this.$(".date_from").val();
            const dateTo = this.$(".date_to").val();
            if (dateFrom) {
                output.date_from = dateFrom;
                save_options.pl_sheet_date_from = dateFrom;
            }
            if (dateTo) {
                output.date_to = dateTo;
                save_options.pl_sheet_date_to = dateTo;
            }

            if (Object.keys(save_options).length === 0) {
                save_options = this.loadReportOptions();
            }
            this.saveSessionOptions(save_options);

            output.branch_list = this.selected_branches.map(branch => branch.id);
            output.tax_added = this.$("#with_tax_data").is(":checked");

            try {
                const datas = await rpc.query({
                    model: 'dynamic.accounting.report',
                    method: 'purchase_report',
                    args: [[this.wizard_id], output],
                });

                if (datas.orders) {
                        debugger;
                    this.$('.table_view_pr').html(QWeb.render('FinanceTable', {
                        filter: datas.filters,
                        order: datas.orders,
                        income_lines: datas.report_lines.income_lines,
                        expense_lines: datas.report_lines.expense_lines,
                        net_lines: datas.report_lines.net_profit,
                    }));
                }
            } catch (error) {
                console.error('Error loading data:', error);
            }
        },

        print_xlsx: async function () {
        debugger;
            const output = {
                date_range: false,
                date_from: this.$(".date_from").val(),
                date_to: this.$(".date_to").val(),
                branch_list: this.selected_branches.map(branch => branch.id),
                tax_added: this.$("#with_tax_data").is(":checked"),
            };

            try {
                const action = await rpc.query({
                    model: 'dynamic.accounting.report',
                    method: 'action_xlsx',
                    args: [[this.wizard_id], output],
                });
                this.do_action(action);
            } catch (error) {
                console.error("Error generating XLSX:", error);
            }
        },

        onClickOpenAccount: async function (ev) {
            const account_id = parseInt(ev.currentTarget.id);
            const output = {
                date_range: false,
                date_from: this.$(".date_from").val(),
                date_to: this.$(".date_to").val(),
                branch_list: this.selected_branches.map(branch => branch.id),
                tax_added: this.$("#with_tax_data").is(":checked"),
            };

            sessionStorage.setItem('from_navigation', '1');
            localStorage.setItem('accounting_report_filters', JSON.stringify(output));

            try {
                const datas = await rpc.query({
                    model: 'account.account',
                    method: 'get_account_view',
                    args: [[account_id], output],
                });
                this.do_action(datas);
            } catch (error) {
                console.error("Error opening account view:", error);
            }
        },
    });

    core.action_registry.add('customreport', ProfitLossReport);
    return ProfitLossReport;
});