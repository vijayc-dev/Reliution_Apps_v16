odoo.define('rcs_t_type_accounting_report.ProfitLossReport', function (require) {
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
        events:{
            'click .xlsx_profit_loss':'print_xlsx',
            'click .apply_profit_loss':'load',
            'click .click_account_line':'onClickOpenAccount',
            'change .with_tax_data':'toggleWithTaxData',
        },

        init: function(parent, action) {
            debugger;
            this._super.apply(this, arguments);
            this.selected_branches = [];
            this.wizard_id = action.context.wizard || null;
            this.actionReportId = action.id;
        },

        print_xlsx: async function () {
            debugger;
            const output = {
                date_range: false};
            output.date_from = this.$(".date_from").val();
            output.date_to = this.$(".date_to").val();
            output.branch_list=(this.selected_branches || []).map(branch => branch.id);
            output.tax_added= this. $("#with_tax_data").is(":checked");

            try {
                const datas = await rpc.query({
                    model : 'dynamic.accounting.report',
                    method : 'action_xlsx',
                    args : [[this.wizard_id],output],
                 });
                this.do_action(datas);
            } catch (error) {
                console.error('Error opening account view:', error);
            }

        },

        start: async function () {
            this.load(true);
        },

        sessionOptionsID: function () {
        debugger;
            return `rcs_t_type_accounting_report:${this.actionReportId}:${session.user_companies.current_company}`;
        },

        saveSessionOptions: function (options) {
        debugger;
            sessionStorage.setItem(this.sessionOptionsID(), JSON.stringify(options));
        },

        sessionOptions: function () {
        debugger;
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
            }

            return loadOptions;
        },

        toggleWithTaxData: function(ev){
        debugger;
            console.log('hii toggleWithTaxData');
        },

        onClickOpenAccount: async function(ev) {
        debugger;
            const output = {
                date_range: false};
            output.date_from = this.$(".date_from").val();
            output.date_to = this.$(".date_to").val();
            output.branch_list=(this.selected_branches || []).map(branch => branch.id);
            output.tax_added= this. $("#with_tax_data").is(":checked");

            // Save filters to localStorage before navigating
            sessionStorage.setItem('from_navigation', '1'); // Mark that user is navigating
            localStorage.setItem('accounting_report_filters', JSON.stringify(output));

            const account_id = parseInt(ev.currentTarget.id);

            try {
                const datas = await rpc.query({
                    model : 'account.account',
                    method : 'get_account_view',
                    args : [[account_id],output],
                 });
                this.do_action(datas);
            } catch (error) {
                console.error('Error opening account view:', error);
            }
        },

        load: async function(){
        debugger;
            console.log("Load Method load");
//            this.load_values= true;
            let output = {
                date_range: false
            };
            let save_options = {};
//            const date_f = document.querySelector(".date_from").value;
//            const date_to = document.querySelector(".date_to").value;
            const date_from = this.$(".date_from").val();
            const date_to = this.$(".date_to").val();
            const tax_added = this.$("#with_tax_data").is(":checked");

            if(date_from){
                output.date_from = date_from;
                save_options.pl_sheet_data_from = date_from;
            }
            if(date_to){
                output.date_to = date_to;
                save_options.pl_sheet_data_to = date_to;
            }
            if (Object.keys(save_options).length === 0) {
                console.log("log")
                save_options = this.loadReportOptions();
            }

            this.saveSessionOptions(save_options);
            if (Object.keys(output).length === 0) {
                output = {'date_from': save_options.pl_sheet_date_from, 'date_to': save_options.pl_sheet_date_to}
            }

            output.branch_list = (this.selected_branches || []).map(branch => branch.id)
            if ($("#with_tax_data")[0]) {
                output.tax_added = $("#with_tax_data")[0].checked;
            }
            try{
                 const datas = await rpc.query({
                    model : 'dynamic.accounting.report',
                    method : 'purchase_report',
                    args : [[this.wizard_id],output],
                 });
                 debugger;
                 if(datas.orders){
                    console.log("datas.orders have a data");
                    this.$('.table_view_pr').html(QWeb.render(
                        'FinanceTableCustom',{
                            filter:datas.filters,
                            order:datas.orders,
                            income_lines:datas.report_lines.income_lines,
                            expense_lines:datas.report_lines.expense_lines,
                            net_lines:datas.report_lines.net_profit
                        }
                    ));

                 }
            } catch (error) {
                console.error('Error loading data:', error);
            }
        },
    });
    core.action_registry.add('customreport', ProfitLossReport);
    return ProfitLossReport;
});
