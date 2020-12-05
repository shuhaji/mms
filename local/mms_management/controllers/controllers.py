# -*- coding: utf-8 -*-
from odoo import http

# class Academic(http.Controller):
#     @http.route('/academic/academic/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/academic/academic/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('academic.listing', {
#             'root': '/academic/academic',
#             'objects': http.request.env['academic.academic'].search([]),
#         })

#     @http.route('/academic/academic/objects/<model("academic.academic"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('academic.object', {
#             'object': obj
#         })