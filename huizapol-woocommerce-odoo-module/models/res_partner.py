from odoo import models, fields


class ResPartnerInheritWoocommerceSalesSynchronization(models.Model):
    _inherit = 'res.partner'

    woocommerce_customer_id = fields.Char(
        string="Woocommerce Client Id", index=True)
