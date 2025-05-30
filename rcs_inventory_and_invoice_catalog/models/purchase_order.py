from collections import defaultdict, Counter
from odoo import models,fields,api
from odoo.osv import expression


class PurchaseOrderCatalog(models.Model):
    _name = 'purchase.order'
    _inherit = ['product.catalog.mixin','purchase.order']

    def _default_order_line_values(self):
        default_data = super()._default_order_line_values()
        new_default_data = self.env['purchase.order.line']._get_product_catalog_lines_data()
        return {**default_data, **new_default_data}

    def _get_product_catalog_domain(self):
        return expression.AND([super()._get_product_catalog_domain(), [('purchase_ok', '=', True)]])

    def _get_product_price_and_data(self, product):
        """ Fetch the product's data used by the purchase's catalog.

        :return: the product's price and, if applicable, the minimum quantity to
                 buy and the product's packaging data.
        :rtype: dict
        """
        self.ensure_one()
        product_infos = {
            'price': product.standard_price,
            'uom': {
                'display_name': product.uom_id.display_name,
                'id': product.uom_id.id,
            },
        }
        if product.purchase_line_warn_msg:
            product_infos['warning'] = product.purchase_line_warn_msg
        if product.purchase_line_warn == "block":
            product_infos['readOnly'] = True
        if product.uom_id != product.uom_po_id:
            product_infos['purchase_uom'] = {
                'display_name': product.uom_po_id.display_name,
                'id': product.uom_po_id.id,
            }
        params = {'order_id': self}
        # Check if there is a price and a minimum quantity for the order's vendor.
        seller = product._select_seller(
            partner_id=self.partner_id,
            quantity=None,
            date=self.date_order and self.date_order.date(),
            uom_id=product.uom_id,
            # ordered_by='min_qty',
            params=params
        )
        if seller:
            product_infos.update(
                # price=seller.price_discounted,
                min_qty=seller.min_qty,
            )
        # Check if the product uses some packaging.
        packaging = self.env['product.packaging'].search(
            [('product_id', '=', product.id), ('purchase', '=', True)], limit=1
        )
        if packaging:
            qty = packaging.product_uom_id._compute_quantity(packaging.qty, product.uom_po_id)
            product_infos.update(
                packaging={
                    'id': packaging.id,
                    'name': packaging.display_name,
                    'qty': qty,
                }
            )
        return product_infos
    def _get_product_catalog_record_lines(self, product_ids):
        grouped_lines = defaultdict(lambda: self.env['purchase.order.line'])
        for line in self.order_line:
            if line.display_type or line.product_id.id not in product_ids:
                continue
            grouped_lines[line.product_id] |= line
        return grouped_lines

    def _get_product_catalog_order_data(self, products, **kwargs):
        res = super()._get_product_catalog_order_data(products, **kwargs)
        for product in products:
            res[product.id] |= self._get_product_price_and_data(product)
        return res

    def _get_product_prices_by_vendor(self, products,qty):
        """
        Returns a dict of {product_id: price}, where price is the vendor price
        if the vendor exists and matches the purchase order partner.
        Otherwise, uses product.standard_price.
        """
        self.ensure_one()
        product_price = {}
        product_min_qty ={}
        vendor_price={}

        for product in products:
            # Try to get seller (vendor) matching PO partner
            seller = product._select_seller(
                partner_id=self.partner_id,
                quantity=None,
                date=self.date_order and self.date_order.date(),
                uom_id=product.uom_id,
                params={'order_id': self}
            )

            if seller:
                ordered_qty = qty.get(product.id)
                if ordered_qty is not None and ordered_qty < seller.min_qty:
                    vendor_price[product.id]=product.standard_price
                else:
                    vendor_price[product.id] = seller.price
                product_price[product.id] = seller.price
                product_min_qty[product.id] = seller.min_qty

            else:
                product_price[product.id] = product.standard_price
                product_min_qty[product.id] = 0
        return product_price,product_min_qty,vendor_price

    def _get_action_add_from_catalog_extra_context(self):

        product_qty = {}
        product_received_qty = {}
        product_ids = []
        for line in self.order_line.filtered(lambda l: l.product_id):
            product_id = line.product_id.id
            product_ids.append(product_id)
            product_qty[product_id] = line.product_uom_qty
            product_received_qty[product_id] = line.qty_received

        all_products = self.env['product.product'].search([])
        product_price, product_min_qty, vendor_price = self._get_product_prices_by_vendor(all_products,product_qty)
        product_standard_price = {product.id: product.standard_price for product in all_products}
        product_counts = Counter(product_ids)
        product_duplicates = {product_id: (count > 1) for product_id, count in product_counts.items()}

        return {
            **super()._get_action_add_from_catalog_extra_context(),
            'display_uom': self.env.user.has_group('uom.group_uom'),
            'precision': self.env['decimal.precision'].precision_get('Product Unit of Measure'),
            'product_catalog_currency_id': self.currency_id.id,
            'product_catalog_digits': self.order_line._fields['price_unit'].get_digits(self.env),
            'search_default_seller_ids': self.partner_id.name,
            'product_qty' : product_qty,
            'productDeliveredQty' : product_received_qty,
            'productPrice' : product_price,
            'read_only' : product_duplicates,
            'product_ids' : all_products.ids,
            'is_purchase': True,
            'vendor_price':vendor_price,
            'productMinQty': product_min_qty,
            'productStandardPrice': product_standard_price,

        }

    def _update_order_line_info(self, product_id, quantity, **kwargs):
        """ Update purchase order line information for a given product or create
        a new one if none exists yet.
        :param int product_id: The product, as a `product.product` id.
        :return: The unit price of the product, based on the pricelist of the
                 purchase order and the quantity selected.
        :rtype: float
        """
        self.ensure_one()
        product_packaging_qty = kwargs.get('product_packaging_qty', False)
        product_packaging_id = kwargs.get('product_packaging_id', False)
        pol = self.order_line.filtered(lambda line: line.product_id.id == product_id)
        if pol:
            if product_packaging_qty:
                pol.product_packaging_id = product_packaging_id
                pol.product_packaging_qty = product_packaging_qty
            elif quantity != 0:
                pol.product_qty = quantity
            elif self.state in ['draft', 'sent']:
                price_unit = self._get_product_price_and_data(pol.product_id)['price']
                pol.unlink()
                return price_unit
            else:
                pol.product_qty = 0
        elif quantity > 0:
            pol = self.env['purchase.order.line'].create({
                'order_id': self.id,
                'product_id': product_id,
                'product_qty': quantity,
                'sequence': ((self.order_line and self.order_line[-1].sequence + 1) or 10),  # put it at the end of the order
            })
            seller = pol.product_id._select_seller(
                partner_id=pol.partner_id,
                quantity=pol.product_qty,
                date=pol.order_id.date_order and pol.order_id.date_order.date() or fields.Date.context_today(pol),
                uom_id=pol.product_uom)
            if seller:
                # Fix the PO line's price on the seller's one.
                pol.price_unit = seller.price
        return pol.price_unit


    def _is_readonly(self):
        """ Return whether the purchase order is read-only or not based on the state.
        A purchase order is considered read-only if its state is 'cancel'.

        :return: Whether the purchase order is read-only or not.
        :rtype: bool
        """
        self.ensure_one()
        return self.state == 'cancel'



