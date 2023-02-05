# -*- coding: utf-8 -*-
{
    'name': "Vehicles Documents",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Abdoulaye GADIAGA",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','fleet'],

    # always loaded
    'data': [
        'data/document_type.xml',
        'security/ir.model.access.csv',
        'views/document_type.xml',
        'views/fleet.xml',
    ],
    'auto_install': True,

}
