from django.shortcuts import render
import os
from subgraph.models import *
from document.models import Document
from search.views import NeoSet, search_by_name, search_rel_by_uuid, search_by_uuid
from py2neo.data import Node, Relationship
import re, json
from django.http import HttpResponse
import pandas as pd
from subgraph.data_extraction import dataframe2dict
from subgraph.translate import translate

# Neo4j Node用到的key
NeoNodeKeys = ['Name', 'Name_zh', 'Name_en', 'PrimaryLabel', 'Area', 'Language']
# Neo4j Relationship用到的key
NeoRelKeys = []
# 这是已经处理好的数据，这里只存储

init = {
    'Person': Person,
    'BaseNode': BaseNode,
    'Project': Project,
    'ArchProject': ArchProject,
    'Document': Document
}


def get_dict(node):
    keylist = []
    for key in dir(node):
        if not re.match(r'__.*__', key):
            keylist.append(key)
    return keylist


# NeoNode: 存在neo4j里的部分 node: 数据源 NewNode: 存在postgre的部分  已经测试过
def create_node(node):
    if 'type' and 'Name' in node:
        # 处理Label类信息
        NeoNode = Node(node['type'])
        node.pop("type")
        NeoNode.add_label('Common')
        NeoNode.add_label('Used')
        NeoNode.update_labels(node['Labels'])
        node.pop("Labels")
        # 处理名字类信息

        def language_setter(node0, language_to, language_from):
            name_tran = 'Name_{}'.format(language_to)
            if name_tran not in node0:
                node0['language'], node0[name_tran] = translate(node0['Name'], language_to, language_from)
        if 'language' not in node:
            node['language'] = 'auto'
        language_setter(node, 'zh', node['language'])
        language_setter(node, 'en', node['language'])

        # 存入postgreSQL固定属性
        NewNode = init[NeoNode['PrimaryLabel']]()
        for key in get_dict(NewNode):
            if key in node:
                setattr(NewNode, key, node[key])
                node.pop(key)

        # 存入Neo4j属性
        NeoNode.update(node)
        NeoSet.tx.create(NeoNode)
        NeoSet.tx.commit()

        # 从Neo4j读取新建节点的uuid， 将其存入postgre
        NeoNode = search_by_name(NeoNode['Name'])
        uuid = NeoNode['uuid']
        setattr(NewNode, 'uuid', uuid)
        NewNode.save()
        return uuid
    else:
        return None


def create_relationship(relationship):
    NeoRel = Relationship(relationship['type'])
    relationship.pop('type')
    NeoRel.update(relationship)
    NeoSet.tx.create(NeoRel)
    NeoSet.tx.commit()
    NeoRel = NeoSet.tx.pull(NeoRel)
    return NeoRel['uuid']


def handle_node(node):
    remote = search_by_uuid(node['uuid'])
    if remote:
        node.pop('uuid')
        remote.update(node)
        return remote['uuid']
    else:
        return create_node(node)


def handle_relationship(relationship):
    remote = search_rel_by_uuid(relationship)
    if remote:
        remote.update(relationship)
    else:
        create_relationship(relationship)


def upload_excel(request):
    excelFile = request.FILES['excelFile']
    a = pd.read_excel(excelFile)
    nodelist = dataframe2dict(a)

    return HttpResponse("upload nodes ok")

