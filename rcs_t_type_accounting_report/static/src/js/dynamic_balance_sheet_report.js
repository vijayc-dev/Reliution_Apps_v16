/** @odoo-module **/

import {
   standardActionServiceProps
} from "@web/webclient/actions/action_service";
import {
   registry
} from '@web/core/registry';
import { rpc
} from "@web/core/network/rpc"
import {
   useService
} from "@web/core/utils/hooks";

import {
   renderToFragment
} from "@web/core/utils/render";
import {
   onWillStart
} from "@odoo/owl";
import {
   Component,
   useState,
   onMounted
} from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { session } from "@web/session";


export class BalanceSheetReport extends Component {
   static template = "BalanceSheet";
   setup() {
   debugger;
      this.rpc = rpc;
      this.orm = useService("orm");
      this.action = useService("action");
      this.report_lines = this.props.action.report_lines;
      this.actionReportId = this.props.action.id;
      this.branch_list = [];
      this.selected_branches = [];
      this.load_values = true;
      this.wizard_id = this.props.action.context.wizard || null;
      this.loadCompanyBranches();
      this.initial_render = true;

      onWillStart(async () => {
            this.branch_list = await this.orm.call('res.company', 'search_read', [[], ['name']]);
      });

      onMounted(() => {
        // const now = new Date();
        // const year = now.getFullYear();
        // const isAfterMarch = now.getMonth() >= 3;
        //
        // const fyStart = new Date(isAfterMarch ? year : year - 1, 3, 1);
        // const fyEnd = new Date(isAfterMarch ? year + 1 : year, 2, 31);
        //
        // const formatDate = (date) =>
        //     `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;

        // $(".date_from")[0].value ||= formatDate(fyStart);
        // $(".date_to")[0].value ||= formatDate(fyEnd);

          const mainReportOptions = this.loadReportOptions();
          $(".date_from")[0].value ||= mainReportOptions['bl_sheet_date_from'];
          $(".date_to")[0].value ||= mainReportOptions['bl_sheet_date_to'];

         const selectBox = $('#many2many-select');
         if (selectBox) {
            $(selectBox).select2({
               placeholder: "Select branches...",
               tags: true,
               width: 'resolve'
            }).on("change", this.onBranchSelectBalance.bind(this));
         }
         const check_lines = $('#click_account_line');
         if (check_lines) {
            this.onClickOpenAccount.bind(this);
         }
      });
      this.loadData(true);
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

                loadOptions.bl_sheet_date_from = formatDate(fyStart);
                loadOptions.bl_sheet_date_to = formatDate(fyEnd);
            }

            return loadOptions;
    }

   async print_xlsx() {
      let output = {
         date_range: false
      };
      if ($(".date_to")[0].value) {
         output.date_to = $(".date_to")[0].value;
      }
      output.branch_list = (this.selected_branches || []).map(branch => branch.id)

      try {
         var action = await this.orm.call(
            'dynamic.accounting.report',
            'balance_action_xlsx',
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
      console.log("button clicked");
      let output = {
         date_range: false
      };
      if ($(".date_to")[0].value) {
         output.date_to = $(".date_to")[0].value;
      }
      output.branch_list = (this.selected_branches || []).map(branch => branch.id);
      const account_id = parseInt(ev.currentTarget.id);

      try {
         var datas = await this.orm.call(
            'account.account',
            'get_account_view_balance_sheet',
            [
               [account_id], output
            ]
         );
         this.env.services.action.doAction(datas);
      } catch (error) {
         console.error('Error opening account view:', error);
      }
   }
   async loadCompanyBranches() {
      try {
         const result = await this.orm.call('res.company', 'search_read', [
            [],
            ['name']
         ]);
         this.branch_list = result || [];
      } catch (error) {
         console.error('Error fetching branch list:', error);
      }
   }


   async loadData(initial_render = true) {
      let output = {
          date_range: false
      };
      let save_options = {};

        if ($(".date_from")[0]) {
            output.date_from = $(".date_from")[0].value;
            save_options.bl_sheet_date_from = $(".date_from")[0].value;
        }
       if ($(".date_to")[0]) {
         output.date_to = $(".date_to")[0].value;
         save_options.bl_sheet_date_to = $(".date_to")[0].value;
       }
       if (Object.keys(save_options).length === 0) {
           save_options = this.loadReportOptions();
       }
       this.saveSessionOptions(save_options);
       if (Object.keys(output).length === 0) {
           output = {'date_from': save_options.bl_sheet_date_from, 'date_to': save_options.bl_sheet_date_to}
       }

      output.branch_list = (this.selected_branches || []).map(branch => branch.id)
      var datas = await this.orm.call(
         'dynamic.accounting.report',
         'balance_sheet_report',
         [
            [this.wizard_id], output
         ]
      );
      if (datas['orders']) {
         self.$('.table_view_pr').html(renderToFragment(
            "BalanceSheetLine", {
               filter: datas['filters'],
               order: datas['orders'],
               liability_lines: datas['report_lines'].liability_lines,
               assets_lines: datas['report_lines'].assets_lines,
               equity_lines:datas['report_lines'].equity_lines,
               net_lines: datas['report_lines'].total_balance,
               profit_loss: datas['report_lines'].profit_loss
            }
         ));
         document.querySelectorAll('.click_account_line').forEach(element => {
            element.addEventListener('click', this.onClickOpenAccount.bind(this));
         });

         console.log(document.querySelectorAll('.click_account_line'));
      }

   }
   onBranchSelectBalance(ev) {

      // Get selected options from Select2
      const selectedOptions = $(ev.target).val();
      this.selected_branches.splice(0); // Clear previous selections

      selectedOptions.forEach(branchId => {
         const branch = this.branch_list.find(branch => branch.id == branchId);
         if (branch) {
            this.selected_branches.push(branch);
         }
      });
   }

   removeBranch(branch_id) {
      // Remove branch from selected list
      this.selected_branches = this.selected_branches.filter(branch => branch.id !== branch_id);
      // Update Select2 to remove the tag
      $($("#many2many-select")).val(
         this.selected_branches.map(branch => branch.id)
      ).trigger("change");
   }

}
// Register the action
registry.category("actions").add("balance_r", BalanceSheetReport);
