from subgraph.models import LocationDoc
from django.core.exceptions import ObjectDoesNotExist
from tools.redis_process import query_location_queue, remove_location_queue
from record.models import LocationsRecord
import googlemaps

token = "AIzaSyAUdQoLyHvvyPaDExQ5gD_KtSvEeiQk0_k"
url = "https://maps.googleapis.com/maps/api/geocode/json?address="
g_map = googlemaps.Client(key=token)


def get_locations():
    locations = query_location_queue()
    locations = [loc for loc in locations if loc]
    locations_done = [location for location in map(get_location, locations) if location]
    remove_location_queue(locations_done)
    return True


# done 07-24 todo 看一下api能不能批量处理 level: 2
def get_location(location):
    loc = str(location)
    try:
        try:
            LocationDoc.objects.get(Name=loc)
        except ObjectDoesNotExist:
            data = g_map.geocode(loc)
            if data:
                loc_info = data[0]
                try:
                    # 查询获得文档的LocId 如果当前名称不存在则加入Alias
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
                return location
            else:
                LocationsRecord.objects.create(Location=location, Is_Done=False)
                return location
    except BaseException:
        return None
