# -*- coding: utf-8 -*-
from odoo import http

# class SalesPersonWaiter(http.Controller):
#     @http.route('/sales_person_waiter/sales_person_waiter/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sales_person_waiter/sales_person_waiter/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sales_person_waiter.listing', {
#             'root': '/sales_person_waiter/sales_person_waiter',
#             'objects': http.request.env['sales_person_waiter.sales_person_waiter'].search([]),
#         })

#     @http.route('/sales_person_waiter/sales_person_waiter/objects/<model("sales_person_waiter.sales_person_waiter"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sales_person_waiter.object', {
#             'object': obj
#         })