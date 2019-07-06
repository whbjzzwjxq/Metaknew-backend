import json
from tools.location import getLocation
from tools.base_tools import NeoSet
from subgraph.logic_class import BaseNode
from django.shortcuts import HttpResponse
import os


def handle_data(line, user):
    data = line
    loc = getLocation(data["Location"])
    Leader = data["Architect"].split(";")
    Leader = [element for element in Leader if element]
    node = data
    node.update({
        "type": "StrNode",
        "PrimaryLabel": "ArchProject",
        "Labels": ["Latin_America", "20century"],
        "Leader": Leader,
        "WorkTeam": Leader,
        "Longitude": loc[0],
        "Latitude": loc[1],
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
    return HttpResponse("Success")
