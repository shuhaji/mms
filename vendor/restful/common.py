"""Common methods"""
import ast
import json
from json import JSONDecodeError
# from simplejson.errors import JSONDecodeError
import werkzeug.wrappers
from odoo.http import request


HTTP_METHOD_OPTION = "OPTIONS"


def valid_response(data, status=200, http_method=None):
    """Valid Response
    This will be return when the http request was successfully processed."""
    data = {
        'count': len(data),
        'data': data
    }
    response = werkzeug.wrappers.Response(
        status=status,
        content_type='application/json; charset=utf-8',
        response=json.dumps(data),
    )
    if http_method == HTTP_METHOD_OPTION:
        # set CORS utk http request dg method options
        # krn default cors-nya mengeset allow header yg terbatas, terpaksa di set manual lg
        set_response_headers(response)
    return response


def set_response_headers(response):
    # not needed anymore, simply set cors="*" on @http.route decorator
    #   these 2 line will automatically added
    response.headers['Access-Control-Allow-Origin'] = "*"
    # response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"

    # response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Headers"] = "Origin, access_token, cache-control, Authorization, " \
                                                       "X-Requested-With, Content-Type, Accept, X-Debug-Mode,"
    # response.headers["Access-Control-Expose-Headers"] = "*"
    return response


def invalid_response(typ, message=None, status=400):
    """Invalid Response
    This will be the return value whenever the server runs into an error
    either from the client or the server."""
    return werkzeug.wrappers.Response(
        status=status,
        content_type='application/json; charset=utf-8',
        response=json.dumps({
            'type': typ,
            'message': message if message else 'wrong arguments (missing validation)',
        }),
    )


def extract_arguments(payloads, offset=0, limit=0, order=None):
    """."""
    fields, domain, payload = [], [], {}
    data = str(payloads)[2:-2]
    try:
        payload = json.loads(data)
    except JSONDecodeError as e:
        pass
    if payload.get('domain'):
        for _domain in payload.get('domain'):
            l, o, r = _domain
            if o == "': '":
                o = '='
            elif o == "!': '":
                o = '!='
            domain.append(tuple([l, o, r]))
    if payload.get('fields'):
        fields += payload.get('fields')
    if payload.get('offset'):
        offset = int(payload['offset'])
    if payload.get('limit'):
        limit = int(payload.get('limit'))
    if payload.get('order'):
        order = payload.get('order')
    return [domain, fields, offset, limit, order]
