# -*- coding: utf-8 -*-
from odoo import http

# class Shift(http.Controller):
#     @http.route('/shift/shift/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/shift/shift/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('shift.listing', {
#             'root': '/shift/shift',
#             'objects': http.request.env['shift.shift'].search([]),
#         })

#     @http.route('/shift/shift/objects/<model("shift.shift"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('shift.object', {
#             'object': obj
#         })