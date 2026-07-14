#-*- coding: utf-8 -*-
{
    'name':         'IT Admin PAC',
    'version': '19.1.2',
    'description':  ''' 
                    Agrega a IT Admin como un PAC adicional para el timbrado de documentos.
                    ''',
    'category':     'Accounting',
    'author':       'IT Admin',
    'website':      'www.itadmin.com.mx',
    'depends':      ['account', 'l10n_mx_edi','account_edi'],
    'data':         ['views/res_company_view.xml',],

    'application':  False,
    'installable':  True,
}
