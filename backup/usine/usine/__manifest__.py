# -*- coding: utf-8 -*-

{
    'name': 'Usine',
    'version': '15.0.7.1.0',
    'category': 'Purchase Management',
    'description': 'Purchase Management ',
    'summary': 'Purchase Management',
    'sequence': '1',
    'author': 'Abdoulaye GADIAGA',
    'license': 'LGPL-3',
    'company': 'Odoo Tech',
    'maintainer': 'Odoo Tech',
    'support': 'gadiagaabdoulaye3@gmail.com',
    'depends': ['base','uom','fleet'],
    'data': [

        'security/usine_security.xml',
        'security/ir.model.access.csv',
        'data/type_operation.xml',
        'data/type_article.xml',
        'data/caisse.xml',
        'data/numero_piece.xml',
        'views/pointage_usine.xml',
        'views/stock.xml',
        'views/vente.xml',
        'views/type_operation.xml',
        'report/payment_report.xml',
        'report/template.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'images': ['static/description/banner.gif'],
}