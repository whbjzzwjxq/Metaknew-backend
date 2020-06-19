import json
from tools.google_map import get_locations
from tools.base_tools import NeoSet
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
    return HttpResponse("Success")
