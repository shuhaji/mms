# -*- coding: utf-8 -*-
from odoo import http

# class HotelId(http.Controller):
#     @http.route('/hotel_id/hotel_id/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hotel_id/hotel_id/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hotel_id.listing', {
#             'root': '/hotel_id/hotel_id',
#             'objects': http.request.env['hotel_id.hotel_id'].search([]),
#         })

#     @http.route('/hotel_id/hotel_id/objects/<model("hotel_id.hotel_id"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hotel_id.object', {
#             'object': obj
#         })