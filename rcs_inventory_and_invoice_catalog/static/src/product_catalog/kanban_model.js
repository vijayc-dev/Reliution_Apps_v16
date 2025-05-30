/** @odoo-module */

//import { Record } from "@web/model/relational_model/record";
import { Record } from '@web/views/relational_model';


//import { RelationalModel } from "@web/model/relational_model/relational_model";
import { RelationalModel } from "@web/views/relational_model";


class ProductCatalogRecord extends Record {
    setup(config, data, options = {}) {
//        debugger;
//        this.productCatalogData = data.productCatalogData;
//        data = { ...data };
//        delete data.productCatalogData;
        const result = super.setup(config, data, options);
        debugger;
    }
}

export class ProductCatalogKanbanModel extends RelationalModel {
    static Record = ProductCatalogRecord;

    setup(config, data, options = {}) {
        const result = super.setup(config, data, options);
        debugger;
    }

    async load(params = {}) {
        const result = await super.load(...arguments);
        debugger;
        const orderLinesInfo = await this.rpc("/product/catalog/order_lines_info", {
                order_id: params.context.order_id,
                product_ids: params.context.product_ids,//[1,2,3,5,4,6],//result.records.map((rec) => rec.id),
                res_model: params.context.product_catalog_order_model,

            });
    }
//    async _loadData(params) {
//    debugger;
//        const result = await super._loadData(...arguments);
//        if (!params.isMonoRecord && !params.groupBy.length) {
//            const orderLinesInfo = await this.rpc("/product/catalog/order_lines_info", {
//                order_id: params.context.order_id,
//                product_ids: result.records.map((rec) => rec.id),
//                res_model: params.context.product_catalog_order_model,
//            });
//            for (const record of result.records) {
//                record.productCatalogData = orderLinesInfo[record.id];
//            }
//        }
//        return result;
//    }
}
