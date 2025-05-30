from odoo import fields, models, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def action_add_from_catalog(self):
        """ Will open the catalog view """
        move = self.env['account.move'].browse(self.env.context.get('order_id'))
        return move.action_add_from_catalog()

    def _get_product_catalog_lines_data(self, **kwargs):
        """
        Return information about account_move_line in `self`.
        If `self` is empty, this method returns only the defaxult value(s) needed for the product
        catalog. In this case, the quantity that equals 0.
        Otherwise, it returns a quantity and a price based on the product of the move line(s) and whether
        the product is read-only or not.
        A product is considered read-only if the order is considered read-only or if `self` contains multiple records.
        Note: This method cannot be called with multiple records that have different products linked.

        :param products: Recordset of `product.product`.
        :param dict kwargs: additional values given for inherited models.
        :rtype: dict
        :return: A dict with the following structure:
            {
                'quantity': float,
                'price': float,
                'readOnly': bool,
                'min_qty': int, (optional)
            }
        """
        if self:
            self.product_id.ensure_one()
            return {
                **self[0].move_id._get_product_price_and_data(self[0].product_id),
                'quantity': sum(
                    self.mapped(
                        lambda line: line.product_uom_id._compute_quantity(
                            qty=line.quantity,
                            to_unit=line.product_id.uom_id,
                        )
                    )
                ),
                'readOnly': self.move_id._is_readonly() or len(self) > 1,
            }
        return {
            'quantity': 0,
        }