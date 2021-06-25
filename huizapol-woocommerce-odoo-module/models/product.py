from odoo import models, fields, api, _
import requests
import json
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    woo_product_id = fields.Char(string="Woocommerce Product Id", index=True)
    woo_product_sku = fields.Char(string="Woocommerce Product Sku", index=True)
    woo_desc = fields.Html(string="Woocommerce Description")

    # def get_product_spareparts(self):
    #     spare_products = [];
    #     for product in self.spare_parts_product_ids:
    #         spare_products.append({
    #             "sku": product.default_code,
    #             "shopify_id": product.woo_product_id
    #         })
    #     return spare_products

    # def get_alternatives_products(self):
    #     alt_products = []
    #     for alt_product in self.alternative_product_ids:
    #         alt_products.append({
    #             "sku": alt_product.default_code,
    #             "shopify_id": alt_product.woo_product_id
    #         })
    #     return alt_products

    # def get_products_accesories(self):
    #     acc_products = []
    #     for acc_product in self.accessory_product_ids:
    #         acc_products.append({
    #             "sku": acc_product.default_code,
    #             "shopify_id": acc_product.woo_product_id
    #         })
    #     return acc_products

    def get_product_parent_tags(self):
        res_categ = []
        for categs in self.categ_id:
            current_category = categs
            while current_category:
                pair_split = {
                    "parent_tag": current_category.parent_id.name,
                    "son_tag": current_category.name
                }
                current_category = current_category.parent_id
                res_categ.append(pair_split)
            # res_categ.append(categs.display_name.split('/'))
        # if res_categ:
        #     if len(res_categ) <= 1:
        #         res_categ = res_categ[0]

        return res_categ

    def get_shopify_data_upload(self):
        _logger.info(_("Started getting data of the product %s") % self.name)
        variants = self.product_variant_ids
        product_image = ''
        # table_image = ''
        # additional_images = []
        # if self.image_1920:
        #    product_image = self.image_1920.decode('utf-8')
        # if self.x_studio_image_shopify:
            # table_image = self.x_studio_image_shopify.decode('utf-8')
        # for image_data in self.product_image_ids:
            # additional_images.append( image_data.image.decode('utf-8') )
        shopify_data_post = {
            "title": self.name,
            # "vendor": self.product_brand_id.mapped('display_name'), # Revisar en que campo está el nombre.
            "woo_product_id": self.woo_product_id,
            "woo_product_sku": self.woo_product_sku,
            "description": self.woo_desc if self.woo_desc else "",
            "tags": self.get_product_parent_tags(),
            # "images": product_image,
            # "table_image": table_image,
            # "additional_images": additional_images,
            #"is_published": True,
            # "product_accesories": self.get_products_accesories(),
            # "product_alternatives": self.get_alternatives_products(),
            # "spare_products": self.get_product_spareparts(),
            "variants": [
                {
                    "sku": variant.default_code,
                    "variant_data": [{variant_attribute.attribute_id.display_name: variant_attribute.name} for
                                     variant_attribute in
                                     variant.product_template_attribute_value_ids],
                    "stock": variant.qty_available,
                    "sales_price": variant.list_price,
                    #"barcode": variant.barcode,
                    #"taxable": bool(variant.taxes_id),
                    "woo_variant_id": variant.woo_variant_id
                } for variant in variants
            ]
        }
        return shopify_data_post

    def upload_product_to_shopify(self):
        for line in self:
            upload_data = line.get_shopify_data_upload()
            if upload_data:
                headers = {'Content-Type': 'application/json'}
                data_json = json.dumps({'params': upload_data})

                try:
                    shopify_product_upload_url = self.env.user.company_id.webhook_post_url + \
                        "/odoo/product-upload"
                    requests.post(url=shopify_product_upload_url,
                                  data=data_json, headers=headers)
                except Exception as e:
                    _logger.error(
                        "Failed to send post request to shopify for upload the product %s, reason : %s" % (
                            self.name, e))
            else:
                _logger.error(
                    _("The upload data is empty for the product %s") % (self.name))


class ProductProduct(models.Model):
    _inherit = 'product.product'

    woo_variant_id = fields.Char(string="Woocommerce variant id", index=True)
