# -*- coding: utf-8 -*-
{
    'name': "Reloj_Registro",

    'summary': """
        reloj_registro""",

    'description': """
        reloj_registro
    """,

    'author': "reloj_registro",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail'],

    # always loaded
    'data': [
        'security/reloj_registro_security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'report/reloj_registro_importador_report_template.xml',
        'report/reloj_registro_importador_report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo/demo.xml',
    ],

    'application': True
}
