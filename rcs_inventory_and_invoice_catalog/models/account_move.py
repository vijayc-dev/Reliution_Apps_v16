from odoo import fields, models, api
from collections import defaultdict, Counter


class AccountMove(models.Model):
    # _inherit = 'account.move'
    _name = 'account.move'
    _inherit = ['product.catalog.mixin', 'analytic.mixin', 'account.move']

    def action_add_from_catalog(self):
        res = super().action_add_from_catalog()
        return res

    def _get_product_prices_by_vendor(self, products):
        """
        Returns a dict of {product_id: price}, where price is the vendor price
        if the vendor exists and matches the purchase order partner.
        Otherwise, uses product.standard_price.
        """
        self.ensure_one()
        product_min_qty = {}

        for product in products:
            # Try to get seller (vendor) matching PO partner
            seller = product._select_seller(
                partner_id=self.partner_id,
                quantity=None,  # use an actual expected quantity
                date=self.invoice_date,
                uom_id=product.uom_id,
                params={'order_id': self}
            )

            if seller:
                product_min_qty[product.id] = seller.min_qty
            else:
                product_min_qty[product.id] = 0

        return product_min_qty

    def _get_action_add_from_catalog_extra_context(self):
        """
        Adds extra context for the action when fetching data from the product catalog.

        This method extends the base action to include additional context, such as the partner's seller ID
        for purchase documents and relevant currency and price digit information.

        :return dict: A dictionary with extra context, including the partner's seller ID (if it's a purchase document),
                  currency ID, and price unit digits.
        """

        product_qty = {}
        product_delivered_qty = {}
        product_ids = []

        for line in self.line_ids.filtered(lambda l: l.product_id ):
            product_id = line.product_id.id
            product_ids.append(product_id)
            product_qty[product_id] = line.quantity
            product_delivered_qty[product_id] = 0
        all_products = self.env['product.product'].search([])
        product_price = {
            product.id: product.standard_price
            if self.move_type in ('in_invoice', 'in_refund')
            else product.lst_price
            for product in all_products
        }

        product_min_qty = self._get_product_prices_by_vendor(all_products)

        product_counts = Counter(product_ids)
        product_duplicates = {product_id: (count > 1) for product_id, count in product_counts.items()}

        res = super()._get_action_add_from_catalog_extra_context()
        if self.is_purchase_document() and self.partner_id:
            res['search_default_seller_ids'] = self.partner_id.name

        res['product_catalog_currency_id'] = self.currency_id.id
        res['product_catalog_digits'] = self.line_ids._fields['price_unit'].get_digits(self.env)
        res['product_qty'] = product_qty
        res['productDeliveredQty'] = product_delivered_qty
        res['productPrice'] = product_price
        res['read_only'] = product_duplicates
        res['product_ids'] = all_products.ids
        res['productMinQty'] = product_min_qty
        if self.move_type in ('in_invoice', 'in_refund'):
            res['is_purchase']= True

        # 'order_line_model_name': 'account.move.line',
        # 'form_view_ref': 'account.view_move_form',

        return res

    def _default_order_line_values(self):
        default_data = super()._default_order_line_values()
        new_default_data = self.env['account.move.line']._get_product_catalog_lines_data()
        return {**default_data, **new_default_data}

    def _get_product_catalog_order_data(self, products, **kwargs):
        """
        Updates the product catalog by adding pricing and additional details for each product.
        This method updates the product catalog by adding pricing and additional details for each product.

        :param products: List of product objects to update.
        :param kwargs: Additional arguments for the base method.
        :return:
            dict: A dictionary where product IDs are keys and their updated data is the value.
        """
        product_catalog = super()._get_product_catalog_order_data(products, **kwargs)
        for product in products:
            product_catalog[product.id] |= self._get_product_price_and_data(product)
        return product_catalog

    def _get_product_price_and_data(self, product):
        """
            This function will return a dict containing the price of the product. If the product is a sale document then
            we return the list price (which is the "Sales Price" in a product) otherwise we return the standard_price
            (which is the "Cost" in a product).
            In case of a purchase document, it's possible that we have special price for certain partner.
            We will check the sellers set on the product and update the price and min_qty for it if needed.
        """

        self.ensure_one()
        product_infos = {'price': product.lst_price if self.is_sale_document() else product.standard_price}

        # Check if there is a price and a minimum quantity for the order's vendor.
        if self.is_purchase_document() and self.partner_id:
            seller = product._select_seller(
                partner_id=self.partner_id,
                quantity=None,
                date=self.invoice_date,
                uom_id=product.uom_id,
                # ordered_by='min_qty',
                params={'order_id': self}
            )
            if seller:
                product_infos.update(
                    price=seller.price,
                    min_qty=seller.min_qty,
                )
        return product_infos

    def _get_product_catalog_record_lines(self, product_ids):
        """
        *This is used to show product quantity in the product.product kanban view.***
        Find and group stock moves by product for the catalog.

        :param product_ids: List of product IDs to search for.
        :return dict: Products linked to their stock move lines.
        """
        grouped_lines = defaultdict(lambda: self.env['account.move.line'])
        for line in self.line_ids:
            if line.display_type == 'product' and line.product_id.id in product_ids:
                grouped_lines[line.product_id] |= line
        return grouped_lines

    def _update_order_line_info(self, product_id, quantity, **kwargs):
        """ Update account_move_line information for a given product or create a
        new one if none exists yet.
        :param int product_id: The product, as a `product.product` id.
        :param int quantity: The quantity selected in the catalog
        :return: The unit price of the product, based on the pricelist of the
                 sale order and the quantity selected.
        :rtype: float
        """
        move_line = self.line_ids.filtered(lambda line: line.product_id.id == product_id)
        if move_line:
            if quantity != 0:
                move_line.quantity = quantity
            elif self.state in {'draft', 'sent'}:
                price_unit = self._get_product_price_and_data(move_line.product_id)['price']
                # The catalog is designed to allow the user to select products quickly.
                # Therefore, sometimes they may select the wrong product or decide to remove
                # some of them from the quotation. The unlink is there for that reason.
                move_line.unlink()
                return price_unit
            else:
                move_line.quantity = 0
        elif quantity > 0:
            move_line = self.env['account.move.line'].create({
                'move_id': self.id,
                'quantity': quantity,
                'product_id': product_id,
            })
        return move_line.price_unit

    def _is_readonly(self):
        """
            Check if the move has been canceled
        """
        self.ensure_one()
        return self.state == 'cancel'
