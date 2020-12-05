# -*- coding: utf-8 -*-
from odoo import http

# class Eventype(http.Controller):
#     @http.route('/eventtype/eventtype/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/eventtype/eventtype/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('eventtype.listing', {
#             'root': '/eventtype/eventtype',
#             'objects': http.request.env['eventtype.eventtype'].search([]),
#         })

#     @http.route('/eventtype/eventtype/objects/<model("eventtype.eventtype"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('eventtype.object', {
#             'object': obj
#         })