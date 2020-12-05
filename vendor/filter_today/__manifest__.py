# -*- coding: utf-8 -*-
# © 2018
#   @Duane(Duanelucky97@gmail.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': "Filter Today",
    "summary": "Add Filter Today",
    "version": "11.0.1.0.0",
    "author": "Duane ",
    "website": "https://github.com/Duane97/filter_today",
    "category": "Extra Tools",
    "depends": ["base", "web"],
    "data": [
        # 'security/ir.model.access.csv',
        "views/header.xml",
    ],

    "qweb": [
        "views/widget/input.xml"
    ],
    "images": ['static/description/icon.png'],
    "license": "AGPL-3",
    "installable": True,
    "application": True,

}
