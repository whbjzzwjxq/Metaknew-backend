from tools.google_map import get_location
from django.shortcuts import HttpResponse


def run_script(request):
    get_location()

    return HttpResponse("ok")
