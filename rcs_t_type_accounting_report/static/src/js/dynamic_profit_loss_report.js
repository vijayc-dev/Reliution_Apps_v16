/** @odoo-module **/

import {
    standardActionServiceProps
} from "@web/webclient/actions/action_service";
import {
    registry
} from '@web/core/registry';
import {
    rpc
} from '@web/core/network/rpc_service';
import {
    useService
} from "@web/core/utils/hooks";
import {
    Component,
    useState,
    onMounted
} from "@odoo/owl";
import {
    onWillStart
} from "@odoo/owl";
import {
    renderToFragment
} from "@web/core/utils/render";
import {
    browser
} from "@web/core/browser/browser";
import {
    session
} from "@web/session";

export class ProfitLossReport extends Component {
    static template = "ProfitLossReport";
    setup() {
        this.actionReportId = this.props.action.id;
        this.report_lines = this.props.action.report_lines;
        this.branch_list = [];
        this.wizard_id = this.props.action.context.wizard || null;
        this.load_values = true;
        this.selected_branches = [];


        this.session = session;
        this.currentCompany = useService("company");
        this.rpc = useService("rpc");
        this.orm = useService("orm");
        this.action = useService("action");
        this.initial_render = true;
        var self = this;
        onWillStart(this.onWillStart);
        onMounted(async () => {
            const mainReportOptions = this.loadReportOptions();
            $(".date_from")[0].value ||= mainReportOptions['pl_sheet_date_from'];
            $(".date_to")[0].value ||= mainReportOptions['pl_sheet_date_to'];
            $("#with_tax_data")[0].checked = mainReportOptions['pl_sheet_tax_added'] || false;

            if (mainReportOptions.pl_sheet_companies && mainReportOptions.pl_sheet_companies.length > 0) {
                this.selected_branches = mainReportOptions.pl_sheet_companies.map(id =>
                    this.branch_list.find(branch => branch.id == id)
                ).filter(Boolean);
            }
            const selectBox = $('#many2many-select');
            if (selectBox.length) {
                $(selectBox).on("change", this.onBranchSelect.bind(this));
            }
            $("#with_tax_data").on("change", this.toggleWithTaxData.bind(this));
            this.loadData(true);
        });
    }

    async onWillStart() {
        this.branch_list = await this.orm.call('res.company', 'search_read', [[['id', 'in', this.currentCompany.activeCompanyIds]],['name']], {
            context: this.session.user_context
        });
    }

    sessionOptionsID() {
        return `rcs_t_type_accounting_report:${ this.actionReportId }:${ session.user_companies.current_company }`;
    }

    saveSessionOptions(options) {
        browser.sessionStorage.setItem(this.sessionOptionsID(), JSON.stringify(options));
    }

    sessionOptions() {
        return JSON.parse(browser.sessionStorage.getItem(this.sessionOptionsID())) || {};
    }

    loadReportOptions() {
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
    }

    async print_xlsx() {
        let output = {
            date_range: false
        };
        if ($(".date_from")[0].value) {
            output.date_from = $(".date_from")[0].value;
        }
        if ($(".date_to")[0].value) {
            output.date_to = $(".date_to")[0].value;
        }

        output.branch_list = (this.selected_branches || []).map(branch => branch.id)
        // if the company not selected then default company is current login company
        if (output.branch_list.length <= 0) {
            output.branch_list = [].concat(this.currentCompany.activeCompanyIds[0]);
        }
        output.tax_added = $("#with_tax_data").checked;

        try {
            var action = await this.orm.call(
                'dynamic.accounting.report',
                'action_xlsx',
                [
                    [this.wizard_id], output
                ]
            );
            this.env.services.action.doAction(action)
        } catch (error) {
            console.error('Error printing XLSX:', error);
        }
    }
    async onClickOpenAccount(ev) {
        let output = {
            date_range: false
        };

        if ($(".date_from")[0]?.value) {
            output.date_from = $(".date_from")[0].value;
        }
        if ($(".date_to")[0]?.value) {
            output.date_to = $(".date_to")[0].value;
        }
        output.branch_list = (this.selected_branches || []).map(branch => branch.id);
        // if the company not selected then default company is current login company
        if (output.branch_list.length <= 0) {
            output.branch_list = [].concat(this.currentCompany.activeCompanyIds[0]);
        }
        output.tax_added = $("#with_tax_data")[0]?.checked || false;

        // Save filters to localStorage before navigating
        sessionStorage.setItem('from_navigation', '1'); // Mark that user is navigating

        localStorage.setItem('accounting_report_filters', JSON.stringify(output));

        const account_id = parseInt(ev.currentTarget.id);

        try {
            const datas = await this.orm.call(
                'account.account',
                'get_account_view',
                [
                    [account_id], output
                ]
            );
            this.env.services.action.doAction(datas);
        } catch (error) {
            console.error('Error opening account view:', error);
        }

    }

    onBranchSelect(ev) {

        // Get selected options from Select2
        const selectedOptions = [].concat($(ev.target).val());
        this.selected_branches.splice(0); // Clear previous selections

        selectedOptions.forEach(branchId => {
            const branch = this.branch_list.find(branch => branch.id == branchId);
            if (branch) {
                this.selected_branches.push(branch);
            }
        });
    }

    toggleWithTaxData(ev) {
        var $checkbox = $(ev.currentTarget);
        var withTaxData = $checkbox.is(':checked');
        // Handle the checkbox change event (e.g., update the report, make an RPC call, etc.)
    }


    async loadData(initial_render = true) {
        this.load_values = true;
        let output = {
            date_range: false
        };
        let save_options = {};

        if ($(".date_from")[0]) {
            output.date_from = $(".date_from")[0].value;
            save_options.pl_sheet_date_from = $(".date_from")[0].value;
        }
        if ($(".date_to")[0]) {
            output.date_to = $(".date_to")[0].value;
            save_options.pl_sheet_date_to = $(".date_to")[0].value;
        }

        if ($("#with_tax_data")[0]) {
            output.tax_added = $("#with_tax_data")[0].checked;
            save_options.pl_sheet_tax_added = $("#with_tax_data")[0].checked;
        }

        if (this.selected_branches.length) {
            save_options.pl_sheet_companies = this.selected_branches.map(b => b.id);
        }

        if (Object.keys(save_options).length === 0) {
            save_options = this.loadReportOptions();
        }
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
            output.branch_list = [].concat(this.currentCompany.activeCompanyIds[0]);
        }
        $('#many2many-select').val(output.branch_list);
        if (this.load_values) {
            var datas = await this.orm.call(
                'dynamic.accounting.report',
                'purchase_report',
                [
                    [this.wizard_id], output
                ]
            );
            if (datas['orders']) {
                self.$('.table_view_pr').html(renderToFragment(
                    "FinanceTable", {
                        filter: datas['filters'],
                        order: datas['orders'],
                        income_lines: datas['report_lines'].income_lines,
                        expense_lines: datas['report_lines'].expense_lines,
                        net_lines: datas['report_lines'].net_profit
                    }
                ));
                document.querySelectorAll('.click_account_line').forEach(element => {
                    element.addEventListener('click', this.onClickOpenAccount.bind(this));
                });


            }
        }
    }
}

// Register the action
registry.category("actions").add("p_r", ProfitLossReport);