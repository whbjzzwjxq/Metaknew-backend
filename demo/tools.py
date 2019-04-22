#-*-coding=utf-8 -*-
from django.http import HttpResponse
import json

def getHttpResponse(status,ret,data=''):
    resp = HttpResponse()
    respData = {'status': status, 'ret': ret, 'data':data}
    resp.content = json.dumps(respData)
    return resp