# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import Counter

from odoo import _, models


class ProductCatalogMixin(models.AbstractModel):
    """ This mixin should be inherited when the model should be able to work
    with the product catalog.
    It assumes the model using this mixin has a O2M field where the products are added/removed and
    this field's co-related model should has a method named `_get_product_catalog_lines_data`.
    """
    _name = 'product.catalog.mixin'
    _description = 'Product Catalog Mixin'

    def action_add_from_catalog(self):
        kanban_view_id = self.env.ref('rcs_inventory_and_invoice_catalog.product_view_kanban_catalog').id
        search_view_id = self.env.ref('rcs_inventory_and_invoice_catalog.product_view_search_catalog').id
        additional_context = self._get_action_add_from_catalog_extra_context()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Products'),
            'res_model': 'product.product',
            'views': [(kanban_view_id, 'kanban'), (False, 'form')],
            'search_view_id': [search_view_id, 'search'],
            'domain': self._get_product_catalog_domain(),
            'context': {**self.env.context, **additional_context},
        }

    def _default_order_line_values(self):
        return {
            'quantity': 0,
            'readOnly': self._is_readonly() if self else False,
        }

    def _get_product_catalog_domain(self):
        """Get the domain to search for products in the catalog.

        For a model that uses products that has to be hidden in the catalog, it
        must override this method and extend the appropriate domain.
        :returns: A list of tuples that represents a domain.
        :rtype: list
        """
        return ['|', ('company_id', '=', False), ('company_id', 'parent_of', self.company_id.id)]

    def _get_product_catalog_record_lines(self, product_ids):
        """ Returns the record's lines grouped by product.
        Must be overrided by each model using this mixin.

        :param list product_ids: The ids of the products currently displayed in the product catalog.
        :rtype: dict
        """
        return {}

    def _get_product_catalog_order_data(self, products, **kwargs):
        """ Returns a dict containing the products' data. Those data are for products who aren't in
        the record yet. For products already in the record, see `_get_product_catalog_lines_data`.

        For each product, its id is the key and the value is another dict with all needed data.
        By default, the price is the only needed data but each model is free to add more data.
        Must be overrided by each model using this mixin.

        :param products: Recordset of `product.product`.
        :param dict kwargs: additional values given for inherited models.
        :rtype: dict
        :return: A dict with the following structure:
            {
                'productId': int
                'quantity': float (optional)
                'productType': string
                'price': float
                'readOnly': bool (optional)
            }
        """
        res = {}
        for product in products:
            res[product.id] = {'productType': product.type}
        return res

    def _get_product_catalog_order_line_info(self, product_ids, **kwargs):
        """ Returns products information to be shown in the catalog.
        :param list product_ids: The products currently displayed in the product catalog, as a list
                                 of `product.product` ids.
        :param dict kwargs: additional values given for inherited models.
        :rtype: dict
        :return: A dict with the following structure:
            {
                'productId': int
                'quantity': float (optional)
                'productType': string
                'price': float
                'readOnly': bool (optional)
            }
        """
        order_line_info = {}
        default_data = self._default_order_line_values()

        for product, record_lines in self._get_product_catalog_record_lines(product_ids).items():
            order_line_info[product.id] = {
               **record_lines._get_product_catalog_lines_data(**kwargs),
               'productType': product.type,
            }
            product_ids.remove(product.id)

        products = self.env['product.product'].browse(product_ids)
        product_data = self._get_product_catalog_order_data(products, **kwargs)
        for product_id, data in product_data.items():
            order_line_info[product_id] = {**default_data, **data}
        return order_line_info

    def _get_common_catalog_product_data(self):
        """Collects product quantity, delivered quantity, and price."""
        product_qty = {}
        product_delivered_qty = {}

        for line in getattr(self, 'order_line', []):
            if line.product_id:
                product_id = line.product_id.id
                product_qty[product_id] = getattr(line, 'product_uom_qty', 0)
                product_delivered_qty[product_id] = getattr(line, 'qty_delivered', 0)

        all_products = self.env['product.product'].search([])

        product_price = {product.id: product.lst_price for product in all_products}
        product_min_qty = {product.id: 0 for product in all_products}

        return product_qty, product_delivered_qty, product_price,product_min_qty

    def _get_action_add_from_catalog_extra_context(self):
        base_context = {
            'product_catalog_order_id': self.id,
            'product_catalog_order_model': self._name,
        }

        if self._name == 'sale.order':
            product_qty, product_delivered_qty, product_price,product_min_qty = self._get_common_catalog_product_data()

            product_ids = [line.product_id.id for line in self.order_line if line.product_id]
            product_counts = Counter(product_ids)
            product_duplicates = {product_id: (count > 1) for product_id, count in product_counts.items()}
            products = self.env['product.product'].search([])
            product_qty_from_pricelist = {item.product_id.id: item.min_quantity for item in self.pricelist_id.item_ids if item.product_id}
            # product_price_from_pricelist = {item.product_id.id: item.fixed_price for item in self.pricelist_id.item_ids if item.product_id}
            product_price_from_pricelist = {
                product.id: (
                    self.pricelist_id.item_ids.filtered(lambda i: i.product_id == product)[0].fixed_price
                    if self.pricelist_id.item_ids.filtered(lambda i: i.product_id == product)
                    else product.list_price
                )
                for product in products
            }

            is_pricelist=False
            if self.pricelist_id:
                is_pricelist=True

            return {
                **base_context,
                'product_catalog_currency_id': self.currency_id.id,
                'product_catalog_digits': self.order_line._fields['price_unit'].get_digits(self.env),
                'product_qty': product_qty,
                'productDeliveredQty': product_delivered_qty,
                'productPrice': product_price,
                'read_only': product_duplicates,
                'is_price_list':is_pricelist,
                'productStandardPrice':product_price_from_pricelist,
                'product_ids': self.env['product.product'].search([]).mapped('id'),
                'productMinQty':product_qty_from_pricelist,
            }

        elif self._name == 'stock.picking':
            move_lines = self.move_ids_without_package
            # product_qty, product_delivered_qty, product_price = self._get_common_catalog_product_data()
            product_qty = {line.product_id.id: line.product_uom_qty for line in move_lines if line.product_id}
            product_delivered_qty = {line.product_id.id: line.quantity_done for line in move_lines if line.product_id}
            all_products = self.env['product.product'].search([])
            product_price = {product.id: product.lst_price for product in all_products}
            product_min_qty = {product.id: 0 for product in all_products}
            product_ids = [line.product_id.id for line in self.move_ids if line.product_id]
            product_counts = Counter(product_ids)
            product_duplicates = {product_id: (count > 1) for product_id, count in product_counts.items()}

            return {
                **base_context,
                'product_qty': product_qty,
                'productDeliveredQty': product_delivered_qty,
                'productPrice': product_price,
                'read_only': product_duplicates,
                'productMinQty':product_min_qty,
                'product_ids': self.env['product.product'].search([]).mapped('id'),

                'product_catalog_currency_id' : self.currency_id.id if hasattr(self, 'currency_id') else False,
                'product_catalog_digits' : self.move_ids._fields['price_unit'].get_digits(self.env) if 'price_unit' in self.move_ids._fields else (0, 2),
                # Set the correct model for catalog order lines
                'order_line_model_name' : 'stock.move',
                # Set the correct product form view to avoid errors when editing products
                'form_view_ref' : 'product.product_normal_form_view',
            }
        return base_context

    def _is_readonly(self):
        """ Must be overrided by each model using this mixin.
        :return: Whether the record is read-only or not.
        :rtype: bool
        """
        return False

    def _update_order_line_info(self, product_id, quantity, **kwargs):
        """ Update the line information for a given product or create a new one if none exists yet.
        Must be overrided by each model using this mixin.
        :param int product_id: The product, as a `product.product` id.
        :param int quantity: The product's quantity.
        :param dict kwargs: additional values given for inherited models.
        :return: The unit price of the product, based on the pricelist of the
                 purchase order and the quantity selected.
        :rtype: float
        """
        return 0
