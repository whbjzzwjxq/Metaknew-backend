from django.shortcuts import render
from py2neo import Graph, NodeMatcher, RelationshipMatcher


class NeoSet:
    graph = Graph('bolt://39.96.10.154:7687', username='neo4j', password='12345678')
    tx = graph.begin()
    Nmatcher = NodeMatcher(graph)
    Rmatcher = RelationshipMatcher(graph)


# uuid搜索
def search_by_uuid(uuid):
    result = NeoSet.Nmatcher.match(uuid=uuid).first()
    return result


# 关键词搜索
def search_by_name(name):
    result = NeoSet.Nmatcher.match(Name=name).first()
    return result


# labels as args,key-value as kwargs
def search_by_dict(*args, **kwargs):
    result = NeoSet.Nmatcher.match(args, kwargs)
    return result


# 模糊查询名字
def fuzzy_name(keyword):
    name = ''
    return name


# 模糊查询关键字 例如属性 标签
def fuzzy_word(keyword):
    word = ''
    return word


# todo 多节点搜索
def search_relation(nodeA,nodeB):
    return 0


# 根据node搜索专题
def search_doc_by_node(node):
    return 0

