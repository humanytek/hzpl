from odoo import models, fields


class SaleOrderInheritOdooStockWoocommerce(models.Model):
    _inherit = 'sale.order'

    woocommerce_sale_order_id = fields.Char(
        string="Woocommerce Order Id", index=True)
