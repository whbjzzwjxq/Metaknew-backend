from tools.redis_conf import red
from subgraph.google_map import get_location
from django.shortcuts import HttpResponse


def run_script(request):
    locations = red.smembers("loc_query_queue")
    locations = [loc.decode() for loc in locations if loc]

    get_location(locations)

    return HttpResponse("ok")
