# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name' : 'Account Cash Flow Statement Report in PDF & Excel Format',
    'version' : '11.0.0.3',
    'category' : 'Accounting',
    'summary': 'This apps helps print account cash flow statement report',
    'depends' : ['base','account','account_invoicing'],
    'author': 'Browseinfo',
    'description': """
    
    Account Cash Flow Statement Report
    Print Account Cash Flow Statement report
    Account Cash Flow Statement print report
    business flow statement. Account flow statement , cash flow report, bank flow report.
    Print Financial Report.Print Accounting report, print cash flow statement, print cash flow report, cashflow report, cash flow pdf report
      
    """,
    'website' : 'www.browseinfo.in',
    "price": 65,
    "currency": 'EUR',
    'data' :[
               'views/account_flow_st_view.xml',
               'views/report.xml',
               'views/report_account_cashflow.xml',
               'data/account_cashflow_report_data.xml',
               'wizard/account_cashflow_save_wizard.xml'
            
    ],      
    'qweb':[
    ],
    'auto_install': False,
    'installable': True,
    "images":["static/description/Banner.png"],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
