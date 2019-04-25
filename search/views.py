from django.http import HttpRequest
from elasticsearch import Elasticsearch
from py2neo import Graph, NodeMatcher, RelationshipMatcher
es = Elasticsearch([{'host': '39.96.10.154', 'port': 9200}])


class NeoSet:
    graph = Graph('bolt://39.96.10.154:7687', username='neo4j', password='12345678')
    tx = graph.begin()
    Nmatcher = NodeMatcher(graph)
    Rmatcher = RelationshipMatcher(graph)


def es_search(index, keyword):
    body = {
        'query': {
            'bool': {
                'must': {

                }
            }
        }
    }


def fuzzy_ask_node(request):
    if request.method == 'GET':
        keyword = request.GET.get('keyword')


def fuzzy_ask_document(request):
    if request.method == 'GET':
        keyword = request.GET.get('keyword')
        index = 'Document'

# uuid搜索


def search_by_uuid(uuid):
    result = NeoSet.Nmatcher.match(uuid=uuid).first()
    return result


# 关键词搜索
def search_by_name(name):
    result = NeoSet.Nmatcher.match(Name=name).first()
    return result


def search_rel_by_uuid(uuid):
    result = NeoSet.Rmatcher.match(uuid=uuid).first()
    return result


# labels as args,key-value as kwargs
def search_by_dict(*args, **kwargs):
    result = NeoSet.Nmatcher.match(args, kwargs)
    return result


# todo 多节点搜索
def search_relation(nodeA,nodeB):
    return 0


# 根据node搜索专题
def search_doc_by_node(node):
    return 0

