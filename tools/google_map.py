from subgraph.models import LocationDoc
from django.core.exceptions import ObjectDoesNotExist
from tools.redis_process import redis
import json
import googlemaps

token = "AIzaSyAUdQoLyHvvyPaDExQ5gD_KtSvEeiQk0_k"
url = "https://maps.googleapis.com/maps/api/geocode/json?address="
g_map = googlemaps.Client(key=token)


def get_location(locations):
    for loc in locations:
        try:
            loc = str(loc)
            try:
                LocationDoc.objects.get(Name=loc)
            except ObjectDoesNotExist:

                data = g_map.geocode(loc)

                if data:
                    loc_info = data[0]
                    try:
                        current = LocationDoc.objects.get(LocId=loc_info["place_id"])
                        if loc not in current.Alias:
                            current.Alias.append(loc)
                        current.save()
                    except ObjectDoesNotExist:
                        new = LocationDoc.objects.create(Name=loc_info["formatted_address"],
                                                         LocId=loc_info["place_id"],
                                                         Alias=[],
                                                         Doc=loc_info)
                        if not loc_info["formatted_address"] == loc:
                            new.Alias.append(loc)
                        new.save()
            redis.srem('loc_query_queue', loc)
        except json.decoder.JSONDecodeError:
            pass
