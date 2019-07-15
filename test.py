from urllib3 import PoolManager
from subgraph.models import LocationDoc
from django.core.cache import cache
import json
token = "&key=AIzaSyAUdQoLyHvvyPaDExQ5gD_KtSvEeiQk0_k"
url = "https://maps.googleapis.com/maps/api/geocode/json?address="


def get_location(locations):
    manager = PoolManager(timeout=60)
    for loc in locations:
        loc = str(loc)
        req = manager.urlopen('GET', url=url+loc+token)
        data = json.loads(req.data)
        LocationDoc.objects.create(
            Name=loc,

        )


get_location(['LanZhou'])
