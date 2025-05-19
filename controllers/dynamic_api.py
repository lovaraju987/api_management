from odoo import http, fields
from odoo.http import request
import json

class DynamicAPI(http.Controller):

    @http.route('/api/<string:endpoint_path>', auth='none', type='http', methods=['GET'], csrf=False)
    def dynamic_api_handler(self, endpoint_path, **kwargs):
        api_key_value = request.httprequest.headers.get("x-api-key")
        ip_address = request.httprequest.remote_addr
        query_string = request.httprequest.query_string.decode()

        api_key = request.env['res.api.key'].sudo().search([
            ('key', '=', api_key_value),
            ('active', '=', True),
            '|', ('expiry_date', '=', False),
                 ('expiry_date', '>=', fields.Date.today())
        ], limit=1)

        if not api_key:
            return self._unauthorized_response(endpoint_path, ip_address, query_string)

        endpoint = request.env['res.api.endpoint'].sudo().search([
            ('url_path', '=', f'/api/{endpoint_path}'),
            ('active', '=', True),
            ('api_key_ids', 'in', api_key.id)
        ], limit=1)

        if not endpoint:
            return self._unauthorized_response(endpoint_path, ip_address, query_string)

        model = endpoint.model_id.model
        fields_allowed = endpoint.field_ids.mapped('name')

        records = request.env[model].sudo().search([], limit=100)
        response_data = [{field: rec[field] for field in fields_allowed} for rec in records]

        request.env['api.access.log'].sudo().create({
            'api_key_id': api_key.id,
            'endpoint': endpoint.url_path,
            'status': 'success',
            'ip_address': ip_address,
            'query_string': query_string,
        })

        return request.make_response(json.dumps(response_data), headers=[('Content-Type', 'application/json')])

    def _unauthorized_response(self, endpoint_path, ip_address, query_string):
        request.env['api.access.log'].sudo().create({
            'api_key_id': False,
            'endpoint': endpoint_path,
            'status': 'unauthorized',
            'ip_address': ip_address,
            'query_string': query_string,
        })
        return request.make_response(json.dumps({"error": "Unauthorized"}), status=401, headers=[('Content-Type', 'application/json')])

