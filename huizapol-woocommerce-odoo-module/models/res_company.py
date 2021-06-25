from odoo import models, fields


class ResCompanyInheritWebhookOdooInventorySalesSynchronisation(models.Model):
    _inherit = 'res.company'

    webhook_post_url = fields.Char(string="Webhook POST URL")

