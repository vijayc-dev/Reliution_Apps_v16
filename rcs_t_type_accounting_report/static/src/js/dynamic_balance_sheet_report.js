odoo.define('rcs_t_type_accounting_report.BalanceSheetReport', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var QWeb = core.qweb;
    var _t = core._t;

    var BalanceSheetReport = AbstractAction.extend({
        contentTemplate: 'BalanceSheet',
        events: {
            'click .xlsx_balance_sheet': 'print_xlsx',
            'click .apply_balance_sheet': 'load',
            'change #many2many-select-balance-sheet': 'onBranchSelectBalance',
            'click .click_account_line': 'onClickOpenAccount',
        },

        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.orm = rpc;
            this.selected_branches = [];
            this.branch_list = [];
            this.report_lines = action.report_lines;
            this.actionReportId = action.id;
            this.wizard_id = action.context.wizard || null;
        },

        start: async function () {
            var self = this;
            await this._super.apply(this, arguments);
            this.branch_list = await this.loadCompanyBranches();
            const options = this.loadReportOptions();
            this.$(".date_from").val(options.bl_sheet_date_from);
            this.$(".date_to").val(options.bl_sheet_date_to);
            const $selectBox = this.$('#many2many-select-balance-sheet');
            $selectBox.select2({
                placeholder: "Select branches...",
                tags: true,
                width: 'resolve'
            });
           //  Get the company for show company related balance sheet
           if (options.bl_sheet_companies && options.bl_sheet_companies.length > 0) {
                this.selected_branches = options.bl_sheet_companies.map(id =>
                    this.branch_list.find(branch => branch.id == id)
                ).filter(Boolean);
            }
            this.load(true);
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
            var loadOptions = this.sessionOptions();
            if (Object.keys(loadOptions).length === 0) {
                const now = new Date();
                const year = now.getFullYear();
                const isAfterMarch = now.getMonth() >= 3;
                const fyStart = new Date(isAfterMarch ? year : year - 1, 3, 1);
                const fyEnd = new Date(isAfterMarch ? year + 1 : year, 2, 31);

                const formatDate = (date) =>
                    `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;

                loadOptions.bl_sheet_date_from = formatDate(fyStart);
                loadOptions.bl_sheet_date_to = formatDate(fyEnd);
                loadOptions.bl_sheet_companies= loadOptions.bl_sheet_companies || [];
            }
            return loadOptions;
        },

        loadCompanyBranches: async function () {
            try {
                return await rpc.query({
                    model: 'res.company',
                    method: 'search_read',
                    args: [[], ['name']]
                });
            } catch (error) {
                console.error('Error fetching branches:', error);
                return [];
            }
        },

        load: async function (initial_render = true) {
            let output = {
                date_range: false
            };
            let save_options = {};

            if (this.$(".date_from").val()) {
                output.date_from = this.$(".date_from").val();
                save_options.bl_sheet_date_from = output.date_from;
            }
            if (this.$(".date_to").val()) {
                output.date_to = this.$(".date_to").val();
                save_options.bl_sheet_date_to = output.date_to;
            }

            if (Object.keys(save_options).length === 0) {
                save_options = this.loadReportOptions();
            }
            if (this.selected_branches.length) {
                save_options.bl_sheet_companies = this.selected_branches.map(b => b.id);
            }
            // Save the data in session
            this.saveSessionOptions(save_options);

            if (Object.keys(output).length === 0) {
                output = {
                    date_from: save_options.bl_sheet_date_from,
                    date_to: save_options.bl_sheet_date_to
                };
            }

            //Pass out the Branch List in xml
            this.$('.balance_sheet_custom_companies_options').html(QWeb.render(
                'branch_ids_balance',
                {
                    branch_list: this.branch_list,
                }
            ));

            // Set the default company as a SelectBox
            if(save_options.bl_sheet_companies){
                this.$('#many2many-select-balance-sheet').val(save_options.bl_sheet_companies);
            }
            output.branch_list = (this.selected_branches || []).map(branch => branch.id);

           //  Call python method to prepare the reports data
            try {
                const datas = await rpc.query({
                    model: 'dynamic.accounting.report',
                    method: 'balance_sheet_report',
                    args: [[this.wizard_id], output],
                });

                if (datas.orders) {
                    this.$('.table_view_pr').html(QWeb.render("BalanceSheetLine", {
                        filter: datas.filters,
                        order: datas.orders,
                        liability_lines: datas.report_lines.liability_lines,
                        assets_lines: datas.report_lines.assets_lines,
                        equity_lines: datas.report_lines.equity_lines,
                        net_lines: datas.report_lines.total_balance,
                        profit_loss: datas.report_lines.profit_loss
                    }));

                    this.$('.click_account_line').on('click', this.onClickOpenAccount.bind(this));
                }
            } catch (error) {
                console.error("Failed to load data:", error);
            }
        },

        print_xlsx: async function () {
            let output = { date_range: false };

            if (this.$(".date_from").val()) {
                output.date_from = this.$(".date_from").val();
            }
            if (this.$(".date_to").val()) {
                output.date_to = this.$(".date_to").val();
            }
            output.branch_list = (this.selected_branches || []).map(branch => branch.id);

            try {
                const action = await rpc.query({
                    model: 'dynamic.accounting.report',
                    method: 'balance_action_xlsx',
                    args: [[this.wizard_id], output],
                });
                this.do_action(action);
            } catch (error) {
                console.error("Error printing XLSX:", error);
            }
        },

        onClickOpenAccount: async function (ev) {
            const account_id = parseInt(ev.currentTarget.id);
            let output = { date_range: false };

            if (this.$(".date_from").val()) {
                output.date_from = this.$(".date_from").val();
            }
            if (this.$(".date_to").val()) {
                output.date_to = this.$(".date_to").val();
            }
            output.branch_list = (this.selected_branches || []).map(branch => branch.id);
            try {
                const datas = await rpc.query({
                    model: 'account.account',
                    method: 'get_account_view_balance_sheet',
                    args: [[account_id], output],
                });
                this.do_action(datas);
            } catch (error) {
                console.error('Error opening account view:', error);
            }
        },

        // Select the Companies and store in selected_branches list
        onBranchSelectBalance: function (ev) {
            const selectedIds = [].concat($(ev.target).val());
            this.selected_branches = selectedIds.map(id =>
                this.branch_list.find(branch => branch.id == id)
            ).filter(Boolean);
        },

        removeBranch: function (branch_id) {
            this.selected_branches = this.selected_branches.filter(branch => branch.id !== branch_id);
            this.$("#many2many-select").val(this.selected_branches.map(b => b.id)).trigger("change");
        }

    });

    core.action_registry.add("BalanceSheetReport", BalanceSheetReport);
    return BalanceSheetReport;
});


