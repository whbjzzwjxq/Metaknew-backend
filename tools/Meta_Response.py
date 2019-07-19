import json
from django.shortcuts import HttpResponse


def get_http_response(status, ret, data=''):
    resp = HttpResponse()
    respData = {'status': status, 'ret': ret, 'data': data}
    resp.content = json.dumps(respData)
    return resp
