# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
import json

def serialize_field(record, field_name, field):
    value = record[field_name]
    if field.type in ('char', 'text', 'selection', 'integer', 'float', 'boolean', 'date', 'datetime', 'monetary'):
        return value
    elif field.type == 'many2one':
        if value:
            try:
                name = value.name_get()[0][1] if hasattr(value, 'name_get') and value.name_get() else str(value.id)
            except Exception:
                name = str(value.id)
            return {'id': value.id, 'name': name}
        return None
    elif field.type in ('one2many', 'many2many'):
        result = []
        for r in value:
            try:
                name = r.name_get()[0][1] if hasattr(r, 'name_get') and r.name_get() else str(r.id)
            except Exception:
                name = str(r.id)
            result.append({'id': r.id, 'name': name})
        return result
    elif field.type == 'binary':
        return bool(value)  # Or encode as base64 if needed
    else:
        return str(value)  # Fallback for unknown types

class DynamicAPI(http.Controller):

    @http.route('/api/<string:endpoint_path>', auth='none', type='http', methods=['GET'], csrf=False)
    def dynamic_api_handler(self, endpoint_path, **kwargs):
        api_key_value = request.httprequest.headers.get('x-api-key')
        ip_address    = request.httprequest.remote_addr
        query_string  = request.httprequest.query_string.decode()

        # 1) validate API key
        api_key = request.env['res.api.key'].sudo().search([
            ('key', '=', api_key_value),
            ('active', '=', True),
            '|', ('expiry_date', '=', False),
                 ('expiry_date', '>=', fields.Date.today())
        ], limit=1)

        if not api_key:
            return self._unauthorized(endpoint_path, ip_address, query_string)

        # 2) find the matching endpoint record
        endpoint = request.env['res.api.endpoint'].sudo().search([
            ('url_path', '=', endpoint_path),
            ('active', '=', True),
            ('api_key_ids', 'in', api_key.id),
        ], limit=1)

        if not endpoint:
            return self._unauthorized(endpoint_path, ip_address, query_string)

        # 3) fetch data
        model_name     = endpoint.model_id.model
        allowed_fields = endpoint.field_ids.mapped('name')
        model_obj      = request.env[model_name]
        records        = model_obj.sudo().search([], limit=100)
        model_fields   = model_obj._fields

        data = []
        for rec in records:
            rec_data = {}
            for fld in allowed_fields:
                field = model_fields.get(fld)
                if field:
                    rec_data[fld] = serialize_field(rec, fld, field)
            data.append(rec_data)

        # 4) log usage
        request.env['api.access.log'].sudo().create({
            'api_key_id':  api_key.id,
            'endpoint':    endpoint.url_path,
            'status':      'success',
            'ip_address':  ip_address,
            'query_string':query_string,
        })

        # 5) return JSON
        return request.make_response(
            json.dumps(data),
            headers=[('Content-Type', 'application/json')]
        )

    def _unauthorized(self, endpoint_path, ip_address, query_string):
        request.env['api.access.log'].sudo().create({
            'api_key_id':  False,
            'endpoint':    endpoint_path,
            'status':      'unauthorized',
            'ip_address':  ip_address,
            'query_string':query_string,
        })
        return request.make_response(
            json.dumps({'error': 'Unauthorized'}),
            status=401,
            headers=[('Content-Type', 'application/json')]
        )
