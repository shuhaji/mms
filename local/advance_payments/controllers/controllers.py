# -*- coding: utf-8 -*-
from odoo import http

# class AdvancePayments(http.Controller):
#     @http.route('/advance_payments/advance_payments/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/advance_payments/advance_payments/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('advance_payments.listing', {
#             'root': '/advance_payments/advance_payments',
#             'objects': http.request.env['advance_payments.advance_payments'].search([]),
#         })

#     @http.route('/advance_payments/advance_payments/objects/<model("advance_payments.advance_payments"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('advance_payments.object', {
#             'object': obj
#         })