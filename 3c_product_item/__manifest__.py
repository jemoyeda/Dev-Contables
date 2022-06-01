# -*- coding: utf-8 -*-
{
    'name': "Change Product Item Design",

    'summary': """
        Change Product Item Design For POS
        """,

    'description': """
        POS Change Product Item Design v15.0
Change Product Item Design make Your Product Item Without Image For Product,
Large Name without image.
        POS,
        POS Shop,
        Point of Sales,
    """,

    'author': "Th3Company",
    'website': "http://th3company.com",

    # Categories can be used to filter modules in modules listing
    # for the full list
    'currency': 'USD',
    'price': '0.0',
    'license': 'LGPL-3',
    'category': 'Point Of Sale',
    'support': 'info@th3company.com',
    'version': '15.0.1.0',
    'images': ['static/description/banner.png'],
    # any module necessary for this one to work correctly
    'depends': ['point_of_sale'],
    'assets': {
        'point_of_sale.assets': [
            "3c_product_item/static/src/css/style.css",
            ],
        'web.assets_qweb': [
           "3c_product_item/static/src/**/*",
            ],
    },
    # only loaded in demonstration mode

    'installable': True,
    'application': True,
    'auto_install': False,
}
