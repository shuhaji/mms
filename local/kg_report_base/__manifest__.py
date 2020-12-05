# -*- coding: utf-8 -*-
{
    'name': "KG CITIS - Report Base",
    'summary': """KG Report Base""",
    'description': """
        Report base addon with stimulsoft
    """,
    'author': "KG-CITIS",
    'website': "",
    'category': 'report',
    'version': '11.0.0.0.1',
    'depends': [
        'account',
    ],
    'data': [
        'views/template.xml',
        'wizards/wizard_kg_report_base.xml',
    ],
    'demo': [

    ],
    'qweb': [
        # 'static/src/xml/base.xml',
        'static/src/xml/report-view.xml',
        'static/src/xml/date-month-year-period-widget.xml'
    ],
}
