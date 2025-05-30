from odoo import fields, models, api
from collections import defaultdict
from odoo.osv import expression
from collections import Counter


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['product.catalog.mixin', 'stock.picking']

    def action_add_from_catalog(self):
        action = super().action_add_from_catalog()
        # kanban_view=self.env.ref('product.product_view_kanban_catalog')
        # list_view = self.env.ref('product.product_product_tree_view')
        # action['views'] = [(kanban_view.id,'kanban'),(list_view.id, 'tree')]
        # action['view_mode'] = 'kanban,tree'
        return action

    def _get_product_catalog_domain(self):
        return expression.AND([super()._get_product_catalog_domain(), [('type', '!=', 'service')]])

    def _default_order_line_values(self ):#child_field=False
        default_data = super()._default_order_line_values()#child_field
        new_default_data = self.env['account.move.line']._get_product_catalog_lines_data()
        return {**default_data, **new_default_data}

    def _get_product_catalog_order_data(self, products, **kwargs):
        product_catalog = super()._get_product_catalog_order_data(products, **kwargs)
        for product in products:
            product_catalog[product.id] |= self._get_product_price_and_data(product)
        return product_catalog

    def _get_product_price_and_data(self, product):
        """
        Return product price for stock picking catalog.
        Typically, we use standard cost as stock moves are internal/purchase/sales logistics.

        Returns:
            dict: A dictionary with the product price, and minimum quantity if available.
        """
        self.ensure_one()
        product_infos = {'price': product.lst_price}  # add a product variant lst_price with extra price of attribute
        return product_infos

    def _get_product_catalog_record_lines(self, product_ids,child_field=False):
        """
           ***This is used to show product quantity in the product.product kanban view.***
           Find and group stock moves by product for the catalog.

           Args:
               product_ids (list of int): List of product IDs to search for.

           Returns:
               dict: Products linked to their stock move lines.
           """
        grouped_lines = defaultdict(lambda: self.env['stock.move'])
        for move in self.move_ids:
            if move.product_id.id in product_ids:
                grouped_lines[move.product_id] |= move
        return grouped_lines

    def _update_order_line_info(self, product_id, quantity, **kwargs):
        """
        Update or create stock.move for the selected product in the catalog.

        Args:
            product_id (int): The ID of the product to update or add.
            quantity (float): The new quantity for the product.
            **kwargs: Extra optional data.

        Returns:
          float: The price unit of the move, or 0.0 if not available.
        """
        move = self.move_ids.filtered(lambda line: line.product_id.id == product_id)
        if move:
            if quantity != 0:
                move.product_uom_qty = quantity
            elif self.state == 'draft':
                price_unit = self._get_product_price_and_data(move.product_id)['price']
                move.unlink()
                return price_unit
            else:
                move.product_uom_qty = 0
        elif quantity > 0:
            move = self.env['stock.move'].create({
                'picking_id': self.id,
                'product_uom_qty': quantity,
                'product_id': product_id,
                'name': self.name or '/',  # Name must not be empty for stock moves
                'product_uom': self.env['product.product'].browse(product_id).uom_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
            })
        return move.product_id.lst_price if hasattr(move, 'price_unit') else 0.0
