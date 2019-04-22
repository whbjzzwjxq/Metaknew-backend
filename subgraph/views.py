from django.shortcuts import render
import os
from subgraph.models import BaseNode, Person
from search.views import NeoSet,search_by_name
from py2neo.data import Node, Relationship
import re, json
from django.http import HttpResponse
# Neo4j用到的key
Neo4jKeys = ['Name', 'Name_zh', 'Name_en', 'PrimaryLabel', 'Area']
# 这是已经处理好的数据，这里只存储

init = {
    'Person': Person,
    'BaseNode': BaseNode
}


def get_dict(node):
    keylist = []
    for key in dir(node):
        if not re.match(r'__.*__', key):
            keylist.append(key)
    return keylist


# NeoNode: 存在neo4j里的部分 node: 数据源 NewNode: 存在postgre的部分  已经测试过
def create_node(node):
    NeoNode = Node(node['type'])
    node.pop("type")
    NeoNode.add_label('Common')
    NeoNode.add_label('Used')
    NeoNode.update_labels(node['Labels'])
    node.pop("Labels")

    for key in Neo4jKeys:
        if key in node:
            NeoNode[key] = node[key]
            node.pop(key)

    NeoSet.tx.create(NeoNode)
    NeoSet.tx.commit()
    NeoNode = search_by_name(NeoNode['Name'])


    node['uuid'] = NeoNode['uuid']
    NewNode = init[NeoNode['PrimaryLabel']]()
    for key in get_dict(NewNode):
        if key in node:
            setattr(NewNode, key, node[key])
    NewNode.save()


def add(request):
    if request.method == 'POST':
        req = json.loads(request.body)
        create_node(req)
    return HttpResponse('200')

