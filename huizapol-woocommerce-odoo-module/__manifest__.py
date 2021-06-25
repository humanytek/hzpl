{
    'name': 'Woocommerce odoo inventory synchronisation and product upload',
    'version': '1.0',
    'summary': 'Synchronise sales and qty of product of odoo and woocommerce and upload you producs to woocommerce',
    'description': 'This module will synchronise the sale order creation of odoo and woocommerce as well as the qtys ajustments and '
                   'will add the feature of uploading the product and all '
                   'its variants using action server, if the upload is successful, it will'
                   'return the woocommerce id of the product',
    'category': 'Inventory, Logistic, Storage, sale',
    'author': '',
    'website': '',
    'license': '',
    'depends': ['base', 'sale', 'sale_management', 'stock', 'product'],
    'data': [
        'views/product.xml',
        'views/res_partner.xml',
        'views/res_company.xml'],
    'installable': True,
    'auto_install': False
}