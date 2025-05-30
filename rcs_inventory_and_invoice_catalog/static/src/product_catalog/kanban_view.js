/** @odoo-module **/

import { kanbanView } from "@web/views/kanban/kanban_view";
import { registry } from "@web/core/registry";

import { ProductCatalogKanbanController } from "./kanban_controller";
import { ProductCatalogKanbanModel } from "./kanban_model";
import { ProductCatalogKanbanRenderer } from "./kanban_renderer";
import { ProductCatalogKanbanRecord } from "./kanban_record";
import { ProductCatalogSearchPanel} from "./search/search_panel";


export const productCatalogKanbanView = {
    ...kanbanView,
    Controller: ProductCatalogKanbanController,
    Model: ProductCatalogKanbanModel,
    Renderer: ProductCatalogKanbanRenderer,
    KanbanRecord: ProductCatalogKanbanRecord,
//    SearchPanel: ProductCatalogSearchPanel,
};

registry.category("views").add("product_kanban_catalog", productCatalogKanbanView);
