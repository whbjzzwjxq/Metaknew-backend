# -*-coding=utf-8 -*-
from django.http import HttpResponse
import json
import requests

map_base_url = 'http://api.map.baidu.com/geocoder/v2/?output=json&ak=I2H9uTTdMe4ARhoMrGzHIWZylZywIiim&address={}'


def getLocation(address):
    res = requests.get(map_base_url.format(address))
    json_data = json.loads(res.text)
    if 'result' in json_data:
        longitude = json_data['result']['location']['lng']
        latitude = json_data['result']['location']['lat']
        return longitude, latitude
    else:
        return 0, 0
