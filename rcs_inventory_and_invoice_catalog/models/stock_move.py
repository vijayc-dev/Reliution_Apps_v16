from odoo import models, fields, api
from odoo.tools.float_utils import float_compare


class StockMove(models.Model):
    _inherit = 'stock.move'

    def action_add_from_catalog(self):
        order = self.env['stock.picking'].browse(self.env.context.get('order_id'))
        return order.action_add_from_catalog()

    def _get_product_catalog_lines_data(self, **kwargs):
        """Return information about sale order lines in `self`.

        If `self` is empty, this method returns only the default value(s) needed for the product
        catalog. In this case, the quantity that equals 0.

        Otherwise, it returns a quantity and a price based on the product of the SOL(s) and whether
        the product is read-only or not.

        A product is considered read-only if the order is considered read-only (see
        ``SaleOrder._is_readonly`` for more details) or if `self` contains multiple records.

        Note: This method cannot be called with multiple records that have different products linked.

        :raise odoo.exceptions.ValueError: ``len(self.product_id) != 1``
        :rtype: dict
        :return: A dict with the following structure:
            {
                'quantity': float,
                'price': float,
                'readOnly': bool,
            }"""

        if self:
            self.product_id.ensure_one()
            return {
                **self[0].picking_id._get_product_price_and_data(self[0].product_id),
                'quantity': sum(
                    self.mapped(
                        lambda move: move.product_uom._compute_quantity(
                            qty=move.product_uom_qty,
                            to_unit=move.product_id.uom_id,
                        )
                    )
                ),
                'readOnly': self.picking_id._is_readonly() or len(self) > 1,
            }
        return {
            'quantity': 0,
        }


