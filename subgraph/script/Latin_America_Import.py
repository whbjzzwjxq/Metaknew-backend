import json
from tools.google_map import get_location
from tools.base_tools import NeoSet
from subgraph.logic_class import BaseNode
from django.shortcuts import HttpResponse
from tools.redis_conf import redis
import os


def handle_data(line, user):
    data = line
    redis.sadd("loc_query_queue", data["Location"])
    Leader = data["Architect"].split(";")
    Leader = [element for element in Leader if element]
    node = data
    node.update({
        "type": "StrNode",
        "PrimaryLabel": "ArchProject",
        "Labels": ["Latin_America", "20century"],
        "Area": "Architecture",
        "Leader": Leader,
        "WorkTeam": Leader,
        "Location": data["Location"],
        "ImportMethod": "Handle",
        "CreateUser": user
    })

    node.pop("Architect")
    return node


def script_latin(request):
    user = request.GET.get("user_id")
    collector = NeoSet()
    path = os.path.join(os.path.dirname(__file__), 'latin_json.json')
    file = open(path, 'r', encoding='utf-8').read()
    lines = json.loads(file)
    nodes = [handle_data(line, user=user) for line in lines]
    results = [BaseNode(collector=collector).create(node=node) for node in nodes]
    collector.tx.commit()
    locations = list(redis.smembers("loc_query_queue"))
    get_location(locations)
    return HttpResponse("Success")
