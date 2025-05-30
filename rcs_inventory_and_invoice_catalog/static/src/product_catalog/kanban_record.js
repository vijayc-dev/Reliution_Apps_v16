/** @odoo-module */
import { useSubEnv } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { useDebounced } from "@web/core/utils/timing";
import { KanbanRecord } from "@web/views/kanban/kanban_record";
import { ProductCatalogOrderLine } from "./order_line/order_line";
import { useState } from "@odoo/owl";


export class ProductCatalogKanbanRecord extends KanbanRecord {
    static components = {
        ...KanbanRecord.components,
        ProductCatalogOrderLine,
    }

    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.debouncedUpdateQuantity = useDebounced(this._updateQuantity, 500, {
            execBeforeUnmount: true,
        });
        this.props.readonly = false;

        this.state = useState({
            productQty: this.props.record.context.product_qty[this.props.record.resId] || 0,
            productDeliveredQty : this.props.record.context.productDeliveredQty[this.props.record.resId] || 0,
            activePrice: this.props.record.context.vendor_price?.[this.props.record.resId] ?? this.props.record.context.productPrice?.[this.props.record.resId] ?? this.props.record.context.productStandardPrice?.[this.props.record.resId] ?? 0,
        });

         var productPrice = this.props.record.context.productPrice[this.props.record.data.id] || 0;
         var productStandardPrice = this.props.record.context.productStandardPrice? this.props.record.context.productStandardPrice[this.props.record.data.id] || 0: 0;
         var read_Only =this.props.record.context.read_only[this.props.record.resId] || false;
         var minimumQty = this.props.record.context.productMinQty[this.props.record.resId] || 1
        useSubEnv({
            currencyId: this.props.record.context.product_catalog_currency_id,
            orderId: this.props.record.context.product_catalog_order_id,
            orderResModel: this.props.record.context.product_catalog_order_model,
            digits: this.props.record.context.product_catalog_digits,
            displayUoM: this.props.record.context.display_uom,
            precision: this.props.record.context.precision,
            read_only : read_Only,
            productId: this.props.record.resId,
            productQty: this.state.productQty,
            productDeliveredQty :this.state.productDeliveredQty,
            is_purchase :this.props.record.context.is_purchase || false,
            minQty : minimumQty,
            productPrice : productPrice,
            is_price_list : this.props.record.context.is_price_list,
            productStandardPrice : productStandardPrice,
            addProduct: this.addProduct.bind(this),
            setQuantity: this.setQuantity.bind(this),
            price_show : this.price_show.bind(this),



        });
    }

    get orderLineComponent() {
        return ProductCatalogOrderLine;
    }

    get productCatalogData() {
        return this.props.record.productCatalogData;
    }

    onGlobalClick(ev) {
        // avoid a concurrent update when clicking on the buttons (that are inside the record)

        if(ev.target.closest(".catalog_three_dot")){
            return;
        }

        // Throttling: Allow clicks only if not already throttled
        if (this.isThrottled) {
            return; // If throttled, ignore the click
        }

        this.isThrottled = true; // Set the throttling flag to true

        setTimeout(() => {
            this.isThrottled = false; // Reset throttling flag after delay (500ms)
        }, 500);

        if(!this.env.read_only){
            if(ev.target.closest('.add-btn')){
                this.props.record.line_qty += 1;
                this._updateQuantity('plus');
            }
            else if(ev.target.closest('.remove-btn')){
                this._updateQuantity('remove')
            }
            else if(ev.target.closest('.quantity')){

            }
            else if(ev.target.closest(".decrement")){
                if(this.state.productDeliveredQty < this.state.productQty){
                    this._updateQuantity('minus');
                }
            }
            else if (ev.target.closest(".increment")) {
                this._updateQuantity('plus');
            }
            else{
                console.log("Global Click");
            }
        }
    }
    price_show(){
        if(this.env.is_purchase){
            if (this.state.productQty >= this.env.minQty || this.state.productQty <= 0) {
                    this.state.activePrice = this.env.productPrice;
                } else {
                    this.state.activePrice = this.env.productStandardPrice;
                }
        }
        else{
            if (this.env.is_price_list && this.state.productQty >= this.env.minQty ) {
                    this.state.activePrice = this.env.productStandardPrice;
                } else {
                    this.state.activePrice = this.env.productPrice;
                }
        }
    }
    async _updateQuantity(icon) {
        if(icon === 'plus'){
            if(this.env.is_purchase && this.state.productQty==0)
            {
                this.state.productQty=this.env.minQty;
            }
            else{
                this.state.productQty += 1;
            }
        }
        else if (icon === 'minus'){
           this.state.productQty -= 1;
        }
        else{
             this.state.productQty = 0;
        }

        this.price_show();
        this._updateQuantityAndGetPrice()
    }

    _updateQuantityAndGetPrice() {
        return this.rpc("/product/catalog/update_order_line_info", this._getUpdateQuantityAndGetPrice());
    }

    _getUpdateQuantityAndGetPrice() {
        return {
            order_id: this.env.orderId,
            product_id: this.env.productId,
            quantity: this.state.productQty,
            res_model: this.env.orderResModel,
        };
    }

    isInOrder() {
    debugger;
        return this.state.productQty !== 0;
    }

    addProduct() {
    debugger;
          this.state.productQty += 1;
    }

    setQuantity(event) {
        debugger;
        var inputElement = document.querySelector('.product-'+this.env.productId);
        var integerInputValue = parseInt(inputElement.value);
        if (this.state.productQty >= this.env.minQty) {
            this.state.activePrice = this.env.productPrice;
        } else {
            this.state.activePrice = this.env.productStandardPrice;
        }
        if (integerInputValue <= 0){
            this.state.productQty = 0;
            this._updateQuantityAndGetPrice();
        }
        if(integerInputValue > this.state.productDeliveredQty)
        {
            if(this.state.productDeliveredQty < this.state.productQty){
                this.state.productQty = parseInt(event.target.value);
                this._updateQuantityAndGetPrice();
            }
        }
        else
        {
            inputElement.value = this.state.productDeliveredQty;
        }

        this.price_show();
    }

}
