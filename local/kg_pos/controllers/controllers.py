# -*- coding: utf-8 -*-
from odoo import http

# class KgPos(http.Controller):
#     @http.route('/kg_pos/kg_pos/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/kg_pos/kg_pos/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('kg_pos.listing', {
#             'root': '/kg_pos/kg_pos',
#             'objects': http.request.env['kg_pos.kg_pos'].search([]),
#         })

#     @http.route('/kg_pos/kg_pos/objects/<model("kg_pos.kg_pos"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('kg_pos.object', {
#             'object': obj
#         })