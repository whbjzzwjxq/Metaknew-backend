import json
from tools.google_map import get_locations
from tools.base_tools import NeoSet
from subgraph.logic_class import BaseNode
from django.shortcuts import HttpResponse
from tools.redis_process import *
import os


def handle_data(line, user):
    data = line
    set_location_queue(data["location"])
    Leader = data["Architect"].split(";")
    Leader = [element for element in Leader if element]
    node = data
    node.update({
        "type": "StrNode",
        "PrimaryLabel": "ArchProject",
        "Labels": ["Latin_America", "20century"],
        "Topic": "Architecture",
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
    path = os.path.join(os.path.dirname(__file__), "latin_json.json")
    file = open(path, "r", encoding="utf-8").read()
    lines = json.loads(file)
    nodes = [handle_data(line, user=user) for line in lines]
    results = [BaseNode(collector=collector).create(node=node) for node in nodes]
    collector.tx.commit()
    locations = get_locations()
    return HttpResponse("Success")
