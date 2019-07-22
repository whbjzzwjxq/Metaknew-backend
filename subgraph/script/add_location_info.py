from tools.redis_process import redis
from tools.google_map import get_location
from django.shortcuts import HttpResponse


def run_script(request):
    locations = redis.smembers("loc_query_queue")
    locations = [loc.decode() for loc in locations if loc]

    get_location(locations)

    return HttpResponse("ok")
