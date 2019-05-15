from django.shortcuts import render
import json
from area import area as area
from django.http import HttpResponse
from django.forms.models import model_to_dict

# Create your views here.
def get_relative_areas(request):
    area_id = json.loads(request.body)['data']['id']

    area_info = area.selectById(area_id)
    relative_areas = area_info.relative_area
    res = []

    for r_areas in relative_areas:
        area_info = {}
        area_info['id'] = int(r_areas)
        area_info['area_name'] = area.selectById(r_areas).areaname
        res.append(area_info)
    return HttpResponse(json.dumps(res), content_type="application/json")

def add_area(request):
    filedata = {'areaname':'area_3','relative_area':[1]}
    res = area.add(filedata)
    return HttpResponse(json.dumps(model_to_dict(res)))