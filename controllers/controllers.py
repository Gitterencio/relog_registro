# -*- coding: utf-8 -*-
# from odoo import http


# class Cochera(http.Controller):
#     @http.route('/cochera/cochera', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cochera/cochera/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('cochera.listing', {
#             'root': '/cochera/cochera',
#             'objects': http.request.env['cochera.cochera'].search([]),
#         })

#     @http.route('/cochera/cochera/objects/<model("cochera.cochera"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cochera.object', {
#             'object': obj
#         })
