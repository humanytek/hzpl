# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
from odoo.http import request
import logging

from odoo import http, tools, exceptions, _

_logger = logging.getLogger(__name__)


class WebhookOdooOrderUpload(http.Controller):

    @http.route(["/woocommerce-upload-order"], type='json', auth='public', methods=['POST'], csrf=False)
    def odoo_upload_order(self, **post):
        _logger.info("Post request received from Woocommerce")
        _logger.info("Creating sale order...")
        try:
            if not request.httprequest.get_data():
                _logger.info("No data found, Abort")
                return
            converted_data = json.loads(
                request.httprequest.get_data().decode('utf-8'))
            data = converted_data
            if not data:
                _logger.info("No data found, Abort")
                return

            _logger.info("Data: %s", str(data))

            woo_order_id = data.get("id")
            sale_order_odoo = request.env['sale.order'].sudo().search(
                [('woocommerce_sale_order_id', '=', woo_order_id)])
            if sale_order_odoo.exists():
                _logger.info("Sale Order already exists, updating order")
                self.update_order(sale_order_odoo, data)

            else:
                _logger.info("Sale Order does not exist, creating order")
                self.create_order(data)

        except Exception as e:
            _logger.info("Error occurred while executing the logic %s" % e)

    def update_order(self, sale_order, data):
        woocommerce_status = data.get("status")
        state_order = sale_order.state
        if state_order == 'draft' and woocommerce_status == 'processing':
            try:
                sale_order.action_confirm()
            except Exception as e:
                _logger.info("Error ocurred while confirming the sale %s" % e)
        if state_order == 'sale' and woocommerce_status == 'enviado':
            # Picking Order <Pending>
            _logger.info("Esta listo para ser aprovado")

        return

    def create_order(self, data):

        # Search if User has already done a sale with us, if not, we create a new res.partner register.
        customerId = data.get('customer-id')
        emailCustomer = data.get('billing-address').get('email')
        shipping_address = data.get("shipping-address")
        billing_address = data.get("billing-address")

        if customerId != 0:
            partner_odoo = request.env['res.partner'].sudo().search(
                [('woocommerce_customer_id', '=', customerId)])
            if not partner_odoo.exists():
                partner_odoo = request.env['res.partner'].sudo().search(
                    [('email', '=', emailCustomer)])
                if not partner_odoo.exists():
                    partner_odoo = self.generate_user(
                        emailCustomer, billing_address)
                partner_odoo.woocommerce_customer_id = customerId

        else:
            partner_odoo = request.env['res.partner'].sudo().search(
                [('email', '=', emailCustomer)])
            if not partner_odoo.exists():
                partner_odoo = self.generate_user(
                    emailCustomer, billing_address)

        billing_address_odoo = partner_odoo

        # Check if shipping address is the same
        shipping_line = billing_address_odoo.street_name
        if shipping_line == shipping_address.get('address_1'):
            shipping_address_odoo = billing_address_odoo
        else:
            shipping_address_odoo = self.generate_user("", shipping_address)
            #shipping_address_odoo.customer = False

        # Creating Sale Order
        cart_content = data.get("cart")
        order_line = self.get_order_lines(cart_content)

        sale_order_odoo = request.env['sale.order'].sudo().create({
            'woocommerce_sale_order_id': data.get("id"),
            'partner_id': partner_odoo.id,
            'partner_invoice_id': billing_address_odoo.id,
            'partner_shipping_id': shipping_address_odoo.id,
            'order_line': order_line
        })

        self.update_order(sale_order_odoo, data)

        return

    def get_order_lines(self, cart):
        res = []
        for cart_item in cart:
            _logger.info("Cart item: %s", str(cart_item))
            product_id = request.env['product.product'].sudo().search(
                [("default_code", "=", cart_item['sku'])])
            if product_id:
                res.append((0, 0, {
                    'product_id': product_id.id,
                    'product_uom_qty': cart_item.get("qty"),
                    'price_unit': cart_item.get("price")
                }))

        return res

    def generate_user(self, email, address):
        partner = request.env['res.partner'].sudo().create({
            'name': address.get('first_name') + " " + address.get('last_name'),
            #'customer': True,
            #'vat': address.get('company'),
            'street_name': address.get('address_1'),
            'zip': address.get('postcode'),
            'city': address.get('city')
            #'over_credit': True,
        })
        _logger.info("User has been created")

        # Country Logic and State <Pending>

        # Phone Logic
        phone = address.get('phone')
        if phone:
            partner.phone = phone

        # Email Logic
        if email:
            partner.email = email

        return partner
