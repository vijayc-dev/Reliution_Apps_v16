/** @odoo-module **/

import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { useService } from "@web/core/utils/hooks";

import { ProductCatalogKanbanRecord } from "./kanban_record";

export class ProductCatalogKanbanRenderer extends KanbanRenderer {
    static template = "ProductCatalogKanbanRenderer";
    static components = {
        ...KanbanRenderer.components,
        KanbanRecord: ProductCatalogKanbanRecord,
    };

    setup() {
        super.setup();
        this.action = useService("action");
    }

    get createProductContext() {
        return {};
    }
    plus(qty=1) {
//        this.updateQuantity(this.productCatalogData.quantity + qty);
        console.log("this is a Plus button click");
    }
    aremoveProduct(qty=1) {
//        this.updateQuantity(this.productCatalogData.quantity + qty);
        console.log("RemoveProduct button click");
    }
    adecreaseQuantity(qty=1) {
//        this.updateQuantity(this.productCatalogData.quantity + qty);
        console.log("DecreaseQuantity button click");
    }
    async createProduct() {
        await this.action.doAction(
            {
                type: "ir.actions.act_window",
                res_model: "product.product",
                target: "new",
                views: [[false, "form"]],
                view_mode: "form",
                context: this.createProductContext,
            },
            {
                onClose: () => this.props.list.model.load(),
            }
        );
    }
}
