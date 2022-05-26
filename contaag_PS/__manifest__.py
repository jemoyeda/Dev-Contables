# -*- coding utf-8 -*-

{

    'name': "Color",
    'description': "Modulo para registrar colores de productos",
    'summary': "Modulo para registrar colores de atributos de productos",
    'author': 'Ing. Hermes Colina',
    'Category': 'General',
    'Version': '1.0.0.0',
    'depends':['base', 'stock'],
    'data':[

            'views/menu_view.xml',
            'views/campos.xml',
            'security/colores_security.xml',
            'security/tallas_security.xml',
            'security/ir.model.access.csv',
        ],

}
