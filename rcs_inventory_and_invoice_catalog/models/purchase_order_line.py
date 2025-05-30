from odoo import models,fields,api


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def action_add_from_catalog(self):
        order = self.env['purchase.order'].browse(self.env.context.get('order_id'))
        return order.action_add_from_catalog()

    def _get_product_catalog_lines_data(self):
        """ Return information about purchase order lines in `self`.

        If `self` is empty, this method returns only the default value(s) needed for the product
        catalog. In this case, the quantity that equals 0.

        Otherwise, it returns a quantity and a price based on the product of the POL(s) and whether
        the product is read-only or not.

        A product is considered read-only if the order is considered read-only (see
        ``PurchaseOrder._is_readonly`` for more details) or if `self` contains multiple records
        or if it has purchase_line_warn == "block".

        Note: This method cannot be called with multiple records that have different products linked.

        :raise odoo.exceptions.ValueError: ``len(self.product_id) != 1``
        :rtype: dict
        :return: A dict with the following structure:
            {
                'quantity': float,
                'price': float,
                'readOnly': bool,
                'uom': dict,
                'purchase_uom': dict,
                'packaging': dict,
                'warning': String,
            }
        """
        if len(self) == 1:
            catalog_info = self.order_id._get_product_price_and_data(self.product_id)
            uom = {
                'display_name': self.product_id.uom_id.display_name,
                'id': self.product_id.uom_id.id,
            }
            catalog_info.update(
                quantity=self.product_qty,
                price=self.price_unit ,
                readOnly=self.order_id._is_readonly(),
                uom=uom,
            )
            if self.product_id.uom_id != self.product_uom:
                catalog_info['purchase_uom'] = {
                'display_name': self.product_uom.display_name,
                'id': self.product_uom.id,
            }
            if self.product_packaging_id:
                packaging = self.product_packaging_id
                catalog_info['packaging'] = {
                    'id': packaging.id,
                    'name': packaging.display_name,
                    'qty': packaging.product_uom_id._compute_quantity(packaging.qty, self.product_uom),
                }
            return catalog_info
        elif self:
            self.product_id.ensure_one()
            order_line = self[0]
            catalog_info = order_line.order_id._get_product_price_and_data(order_line.product_id)
            catalog_info['quantity'] = sum(self.mapped(
                lambda line: line.product_uom._compute_quantity(
                    qty=line.product_qty,
                    to_unit=line.product_id.uom_id,
            )))
            catalog_info['readOnly'] = True
            return catalog_info
        return {'quantity': 0}