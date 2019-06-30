from search.views import NeoSet, search_rel_exist, search_by_uuid
from py2neo.data import Relationship
from django.http import HttpResponse
import pandas as pd
from script.data_extraction import dataframe2dict
from subgraph.logic_class import NeoNode
from tools import base_tools
import json


# NeoNode: 存在neo4j里的部分 node: 数据源 NewNode: 存在postgre的部分  已经测试过


def create_relationship(relationship):
    # source 和 target 是Node对象
    source = relationship["source"]
    target = relationship["target"]
    relationship.update({'uuid': base_tools.get_uuid(source['Name'] + 'to' + target['Name'])})
    NeoRel = Relationship(source, relationship['type'], target)
    relationship.pop('type')
    relationship.pop('source')
    relationship.pop('target')
    NeoRel.update(relationship)
    collector = NeoSet()
    collector.tx.create(NeoRel)
    collector.tx.commit()
    return NeoRel


def handle_node(node):
    if 'uuid' in node:
        remote = search_by_uuid(node['uuid'])
        if remote:
            node.pop('uuid')
            remote.update(node)
            return remote
        else:
            return create_node(node)
    else:
        return create_node(node)


def handle_relationship(relationship):
    remote = search_rel_exist(relationship)
    if remote:
        if "uuid" in relationship:
            relationship.pop('uuid')
        remote.update(relationship)
        return remote
    else:
        return create_relationship(relationship)


def upload_excel(request):
    excelFile = request.FILES['excelFile']
    a = pd.read_excel(excelFile)
    nodelist = dataframe2dict(a)

    return HttpResponse("upload nodes ok")


def add_node(request):
    collector = base_tools.NeoSet()
    data = json.loads(request.body, encoding='utf-8')['data']
    user = json.loads(request.body, encoding='utf-8')['user']  # todo 用户注册登录
    node = NeoNode(collector=collector)
    try:
        node.create(user=user, node=data)
        node.collector.tx.commit()
        return HttpResponse("add node success")
    except AssertionError:
        return HttpResponse("bad information")
