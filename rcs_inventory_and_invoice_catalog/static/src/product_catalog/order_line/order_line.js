///** @odoo-module */
//import { Component } from "@odoo/owl";
//import { formatFloat, formatMonetary } from "@web/views/fields/formatters";
//debugger;
//
//export const ProductCatalogOrderLine = {
//    template: "ProductCatalogOrderLine",
//    props: ["productId", "quantity", "price", "productType", "readOnly", "warning"],
//
//    methods: {
//        _onFocus(ev) {
//            ev.target.select();
//        },
//        isInOrder() {
//        debugger;
//            return this.props.quantity !== 0;
//        },
//
//        getPrice() {
//            const { currencyId, digits } = this.env;
//            return formatMonetary(this.props.price, { currencyId, digits });
//        },
//
//        getQuantity() {
//            const digits = [false, 2]; // Adjust as needed
//            const options = { digits, decimalPoint: ".", thousandsSep: "" };
//            return parseFloat(formatFloat(this.props.quantity, options));
//        },
//
//        getDisableRemove() {
//            return false;
//        },
//
//        getDisabledButtonTooltip() {
//            return "";
//        },
//    },
//};



/** @odoo-module **/

import { Component, useEnv } from "@odoo/owl";
import { formatFloat, formatMonetary } from "@web/views/fields/formatters";

export class ProductCatalogOrderLine extends Component {
//    static template = "ProductCatalogOrderLine";
    static props = {
        productId: Number,
        quantity: Number,
        price: Number,
        productType: String,
        readOnly: Boolean,
        warning: { type: String, optional: true },
    };

    setup() {
    debugger;
        this.env = useEnv();
    }

    _onFocus(ev) {

        ev.target.select();
    }

        isInOrder() {
        debugger;
            return this.props.quantity !== 0;
        }

    getPrice() {
    debugger;
        const { currencyId, digits } = this.env;
        return formatMonetary(this.props.price, { currencyId, digits });
    }

    getQuantity() {
    debugger;
        const digits = [false, 2]; // Adjust as needed
        const options = { digits, decimalPoint: ".", thousandsSep: "" };
        return parseFloat(formatFloat(this.props.quantity, options));
    }

    getDisableRemove() {
    debugger;
        return false;
    }

    getDisabledButtonTooltip() {
    debugger;
        return "";
    }
}

ProductCatalogOrderLine.template = "rcs_inventory_and_invoice_catalog.ProductCatalogOrderLine";
