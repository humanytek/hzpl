from odoo.tools.float_utils import float_is_zero
from odoo import models, fields, api, _
import requests
import json
import logging

_logger = logging.getLogger(__name__)


class StockMoveLineInheritShopifyOdooInventorySalesSynchronisation(models.Model):
    _inherit = 'stock.move.line'

    def send_data_to_webserver(self):
        for line in self:
            if line.product_id.woo_variant_id:
                product_variant_id=line.product_id.woo_variant_id
            else:
                product_variant_id=False
            data = {'product_variant_id': product_variant_id, 'sku': line.product_id.default_code,
                    'stock_qty': line.product_id.qty_available,
                    'price': line.product_id.list_price,
                    'product_tmpl_id':line.product_id.product_tmpl_id.woo_product_id }
            _logger.info("Loading data to webservice %s" % data)
            headers = {'Content-Type': 'application/json'}
            data_json = json.dumps({'params': data})
            try:
                stock_url_post = self.env.user.company_id.webhook_post_url + '/odoo/stock-update'
                requests.post(url=stock_url_post,
                              data=data_json, headers=headers)
            except Exception as e:
                _logger.error(
                    "Failed to send post request to shopify webservice, reason : %s" % e)

    def _action_done(self):
        res = super(
            StockMoveLineInheritShopifyOdooInventorySalesSynchronisation, self)._action_done()
        for stock_move_line in self.exists():
            if stock_move_line:
                stock_move_line.send_data_to_webserver()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """A function like create of the original in order to track the changing of done moves qty"""
        mls = super(
            StockMoveLineInheritShopifyOdooInventorySalesSynchronisation, self).create(vals_list)
        # for vals in vals_list:
        #     print("Hola")
        for ml in mls:
            if ml:
                if ml.state == 'done':
                    if ml.product_id.type == 'product':
                        ml.send_data_to_webserver()
        return mls

    def write(self, vals):
        """ A write function like in the original to update products qtys in case of modification in done state of move
        """
        res = super(
            StockMoveLineInheritShopifyOdooInventorySalesSynchronisation, self).write(vals)
        triggers = [
            ('location_id', 'stock.location'),
            ('location_dest_id', 'stock.location'),
            ('lot_id', 'stock.production.lot'),
            ('package_id', 'stock.quant.package'),
            ('result_package_id', 'stock.quant.package'),
            ('owner_id', 'res.partner')
        ]
        updates = {}
        for key, model in triggers:
            if key in vals:
                updates[key] = self.env[model].browse(vals[key])

        if updates or 'qty_done' in vals:

            mls = self.filtered(lambda ml: ml.move_id.state ==
                                'done' and ml.product_id.type == 'product')
            if not updates:  # we can skip those where qty_done is already good up to UoM rounding
                mls = mls.filtered(lambda ml: not float_is_zero(ml.qty_done - vals['qty_done'],
                                                                precision_rounding=ml.product_uom_id.rounding))
            for ml in mls:
                if ml:
                    ml.send_data_to_webserver()
        return res
