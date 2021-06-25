# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
from odoo.http import request
import logging

from odoo import http, tools, exceptions, _

_logger = logging.getLogger(__name__)


class ShopifyOdooProductUploadResponse(http.Controller):

    @http.route(["/webhook_product_upload_results"], type='json', auth="public", methods=['POST'], csrf=False)
    def synchronise_odoo(self, **post):
        _logger.info("Post request received from a response of product upload")
        try:
            if not request.httprequest.get_data():
                _logger.info("No data found, Abort")
            converted_data = json.loads(
                request.httprequest.get_data().decode('utf-8'))
            error = converted_data.get('error')
            if error:
                if error.get('status'):
                    _logger.info("Response with an error: %s" %
                                 error.get('errorMessage'))
                    return
            data = converted_data.get('payload')
            if not data:
                _logger.info("No data found, Abort")
                return

            product_template_id = self.get_product_template(data)
            if product_template_id:
                _logger.info("Found product template by the name %s" %
                             product_template_id.name)
                product_template_id.woo_product_id = data.get(
                    'woo_product_id')
                response_variants = data.get('variants')
                for response_variant in response_variants:
                    if response_variant.get('sku'):
                        _logger.info("Iterating variants:")
                        for variant in product_template_id.product_variant_ids:
                            _logger.info("Im searching in variants")
                            if variant.default_code == response_variant['sku']:
                                variant.woo_variant_id = response_variant.get(
                                    'variant_id')
                                break

        except Exception as e:
            _logger.info("Error occurred while executing the logic %s" % e)

    def get_product_template(self, data):
        # since all the variants will have the same template,
        # we need tp take only the first variant and search for it, and get its
        # template
        if data.get('variants'):
            first_variant = data['variants'][0]
            if first_variant.get('sku'):
                variant_id = request.env['product.product'].sudo().search([('default_code', '=', first_variant['sku'])],
                                                                          limit=1)
                if variant_id:
                    product_template_id = variant_id.product_tmpl_id
                    return product_template_id
        else:
            product_template_id = request.env['product.template'].sudo().search([('default_code', '=', data['sku'])], limit=1)
            return product_template_id
